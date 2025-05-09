import asyncio
import json
import logging
from dataclasses import dataclass

from telegram import Update
from telegram.ext import ContextTypes
from serpapi import GoogleSearch
from trafilatura import extract, fetch_url

from app.config import settings
from bot.decorators import authorized
from llm.agent import Agent
from llm.prompts.digin_prompts import (
    SEARCH_PLAN_PROMPT,
    PAGE_SUMMARIZER_PROMPT,
    SYNTHESIS_PROMPT,
)

# Setup logger
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str


@dataclass
class CleanedPageContent:
    result: SearchResult
    cleaned_text: str


@dataclass
class SummerizedPageContent:
    result: SearchResult
    summary: str


@dataclass
class FinalReport:
    original_query: str
    synthesized_answer: str
    all_sources_consulted: list[SearchResult]


@authorized
async def digin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /digin command.
    """
    user_query = update.message.text.replace("/digin", "").strip()

    if not await _validate_user_query(update, user_query):
        return

    search_queries = await _plan_and_notify_searches(update, user_query)
    if not search_queries:
        return

    search_tasks = []
    for query in search_queries:
        task = asyncio.to_thread(
            _search_with_serpapi,
            query,  # Pass arguments positionally to asyncio.to_thread
            settings.DIGIN_MAX_RESULTS,
        )
        search_tasks.append(task)

    all_search_results = await _execute_and_process_searches(update, search_tasks)
    if not all_search_results:
        return

    cleaned_pages = await _fetch_and_clean_and_notify(update, all_search_results)
    if not cleaned_pages:
        return

    summaries = await _summarize_and_notify_pages(update, cleaned_pages)
    if not summaries:
        return

    await _synthesize_and_send_report(update, user_query, summaries)


async def _plan_searches(user_query: str) -> list[str]:
    """
    Plans search queries based on the user's input.
    """
    search_planner_agent = Agent(system_prompt=SEARCH_PLAN_PROMPT)
    search_plan_str = await asyncio.to_thread(search_planner_agent.process, user_query)
    try:
        search_plan = json.loads(search_plan_str)
        return search_plan.get("search_queries", [])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse search plan JSON: {e}", exc_info=True)
        logger.error(f"Received string was: {search_plan_str}")
        return []


async def _fetch_and_clean_pages(
    search_results: list[SearchResult],
) -> list[CleanedPageContent]:
    """
    Fetches and cleans the content of web pages from search results.
    """
    cleaned_pages = []
    for result in search_results:
        try:
            # Download the page content using trafilatura's fetch_url
            downloaded_file = await asyncio.to_thread(fetch_url, result.url)
            if downloaded_file:
                # Extract text content from the downloaded file
                cleaned_text = await asyncio.to_thread(extract, downloaded_file)
                if cleaned_text:  # Ensure we have some text after extraction
                    cleaned_page = CleanedPageContent(
                        result=result,
                        cleaned_text=cleaned_text,
                    )
                    cleaned_pages.append(cleaned_page)
                else:
                    logger.warning(
                        f"No content extracted from {result.url}. Extraction might have failed or page was empty."
                    )
            else:
                logger.warning(f"Failed to download content from {result.url}.")
        except Exception as e:
            logger.error(f"Error fetching or cleaning {result.url}: {e}", exc_info=True)
            continue
    return cleaned_pages


async def _summarize_pages(
    cleaned_pages: list[CleanedPageContent],
) -> list[SummerizedPageContent]:
    """
    Summarizes the content of cleaned web pages.
    """
    summaries = []
    summarizer_agent = Agent(system_prompt=PAGE_SUMMARIZER_PROMPT)
    for cleaned_page in cleaned_pages:
        try:
            summary_result = await asyncio.to_thread(
                summarizer_agent.process, cleaned_page.cleaned_text
            )
            if summary_result:
                summarized_page = SummerizedPageContent(
                    result=cleaned_page.result,
                    summary=summary_result,
                )
                summaries.append(summarized_page)
            else:
                logger.warning(
                    f"No summary generated for {cleaned_page.result.url}. Summarization might have failed or content was unsuitable."
                )
        except Exception as e:
            logger.error(
                f"Error summarizing {cleaned_page.result.url}: {e}", exc_info=True
            )
            continue
    return summaries


async def _synthesize_report(
    original_query: str, summarized_pages: list[SummerizedPageContent]
) -> FinalReport:
    """
    Synthesizes a final report from the original query and summarized page content.
    """
    if not summarized_pages:
        logger.warning(
            f"No summaries available to synthesize report for query: '{original_query}'."
        )
        return FinalReport(
            original_query=original_query,
            synthesized_answer="Could not gather enough information to provide an answer.",
            all_sources_consulted=[],
        )

    context_for_synthesis = f'Original User Query: "{original_query}"\n\n'
    context_for_synthesis += "Please synthesize the information from the following summaries to answer the user's query. Cite the source title or URL when using information from a specific source.\n\n"

    for i, summarized_page in enumerate(summarized_pages):
        context_for_synthesis += f"Source {i+1}:\n"
        context_for_synthesis += f"Title: {summarized_page.result.title}\n"
        context_for_synthesis += f"URL: {summarized_page.result.url}\n"
        context_for_synthesis += f"Summary:\n{summarized_page.summary}\n\n"

    synthesis_agent = Agent(system_prompt=SYNTHESIS_PROMPT)
    synthesized_output = await asyncio.to_thread(
        synthesis_agent.process, context_for_synthesis
    )

    unique_source_results = []
    seen_urls = set()
    for sp in summarized_pages:
        if sp.result.url not in seen_urls:
            unique_source_results.append(sp.result)
            seen_urls.add(sp.result.url)

    return FinalReport(
        original_query=original_query,
        synthesized_answer=synthesized_output,
        all_sources_consulted=unique_source_results,
    )


def _format_report(report: FinalReport) -> str:
    """
    Formats the final report into a text string for the user.
    """
    response_text = report.synthesized_answer
    if report.all_sources_consulted:
        response_text += "\n\nSources Consulted:\n"
        for src in report.all_sources_consulted:
            response_text += f"- {src.title}: {src.url}\n"
    return response_text


def _search_with_serpapi(query: str, max_results: int) -> list[SearchResult]:
    """
    Search using SerpApi (Google Search) for the given query.
    """
    params = {
        "q": query,
        "engine": "google",
        "num": max_results,
        "api_key": settings.SERPAPI_API_KEY,
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])

        return [
            SearchResult(title=r.get("title", "No Title"), url=r.get("link", ""))
            for r in organic_results
            if r.get("link")
        ]
    except Exception as e:
        logger.error(f"SerpApi search failed for query '{query}': {e}", exc_info=True)
        return []


async def _validate_user_query(update: Update, user_query: str) -> bool:
    """
    Validates the user query and sends a message if invalid.
    Returns True if valid, False otherwise.
    """
    if not user_query or user_query.strip() == "":
        await update.message.reply_text(
            "🎯 My digital shovel is poised and ready, but I can't dig for... well, nothing! "
            "What treasure are we unearthing today? Please provide a query."
        )
        return False
    return True


async def _plan_and_notify_searches(update: Update, user_query: str) -> list[str]:
    """
    Plans search queries and notifies the user.
    Returns the list of search queries or an empty list if planning fails.
    """
    search_queries = await _plan_searches(user_query)

    if not search_queries:
        await update.message.reply_text(
            "🤔 Hmm, my digital compass seems to be spinning in circles! "
            "Perhaps try a different angle or a more specific query?"
        )
        return []
    else:
        await update.message.reply_text(
            "🗺️ I've sketched out my treasure map! Time to start digging!"
        )
        return search_queries


async def _execute_and_process_searches(
    update: Update, search_tasks: list
) -> list[SearchResult]:
    """
    Executes search tasks, processes results, and notifies the user.
    Returns a list of unique SearchResult objects or an empty list if no results.
    """
    await update.message.reply_text(
        "⛏️ *clink clink* I'm digging through the digital dirt for you..."
    )

    search_results_per_query = await asyncio.gather(*search_tasks)

    all_search_results = []
    for search_result in search_results_per_query:
        if search_result:  # _search_with_serpapi can return [] on error
            all_search_results.extend(search_result)

    if not all_search_results:
        await update.message.reply_text(
            "😅 Looks like I hit bedrock! Couldn't find any nuggets of wisdom for your query."
        )
        return []
    else:
        await update.message.reply_text(
            "💎 Eureka! Found some shiny information! Let me polish it up..."
        )
        return all_search_results


async def _fetch_and_clean_and_notify(
    update: Update, search_results: list[SearchResult]
) -> list[CleanedPageContent]:
    """
    Fetches and cleans pages from search results and notifies the user.
    Returns a list of CleanedPageContent objects or an empty list if cleaning fails.
    """
    await update.message.reply_text(
        "✨ Sparkling clean! Now let me organize these gems..."
    )

    cleaned_pages = await _fetch_and_clean_pages(search_results)
    if not cleaned_pages:
        await update.message.reply_text(
            "🧹 Oops! My digital broom broke while cleaning up the information!"
        )
        return []
    return cleaned_pages


async def _summarize_and_notify_pages(
    update: Update, cleaned_pages: list[CleanedPageContent]
) -> list[SummerizedPageContent]:
    """
    Summarizes cleaned pages and notifies the user.
    Returns a list of SummarizedPageContent objects or an empty list if summarization fails.
    """
    await update.message.reply_text(
        "📚 Perfect! Now let me weave these threads into a beautiful tapestry..."
    )

    summaries = await _summarize_pages(cleaned_pages)
    if not summaries:
        await update.message.reply_text(
            "📝 My digital quill ran out of ink while summarizing!"
        )
        return []
    return summaries


async def _synthesize_and_send_report(
    update: Update, user_query: str, summaries: list[SummerizedPageContent]
):
    """
    Synthesizes the final report and sends it to the user.
    """
    report = await _synthesize_report(user_query, summaries)

    if not report:
        await update.message.reply_text(
            "🧩 My digital puzzle pieces just won't fit together!"
        )
        return

    formatted_report = _format_report(report)
    await update.message.reply_text(formatted_report)
