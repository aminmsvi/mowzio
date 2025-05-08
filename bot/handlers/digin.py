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
            try:
                summary_text = json.loads(summary_result).get("summary", "")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse summary JSON: {e}", exc_info=True)
                logger.error(f"Received string was: {summary_result}")
                summary_text = ""
            if summary_text:
                summarized_page = SummerizedPageContent(
                    result=cleaned_page.result,
                    summary=summary_text,
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

    try:
        final_answer_text = json.loads(synthesized_output).get(
            "synthesized_report_text", "Could not synthesize an answer."
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse synthesized output JSON: {e}", exc_info=True)
        logger.error(f"Received string was: {synthesized_output}")
        final_answer_text = "Could not synthesize an answer."

    # Ensure unique sources, considering some results might be from the same URL due to multiple search queries
    # The SearchResult dataclass needs to be hashable for set to work, or implement __eq__ and __hash__.
    # For now, let's assume SearchResult is hashable or convert to a tuple of its fields.
    unique_source_results = []
    seen_urls = set()
    for sp in summarized_pages:
        if sp.result.url not in seen_urls:
            unique_source_results.append(sp.result)
            seen_urls.add(sp.result.url)

    return FinalReport(
        original_query=original_query,
        synthesized_answer=final_answer_text,
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


@authorized
async def digin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /digin command.
    """
    user_query = update.message.text.replace("/digin", "").strip()
    if not user_query or user_query.strip() == "":
        await update.message.reply_text(
            "My digital shovel is poised and ready, but I can't dig for... well, nothing! "
            "What treasure are we unearthing today? Please provide a query."
        )
        return

    search_queries = await _plan_searches(user_query)

    all_search_results = []
    for query in search_queries:
        results_for_query = _search_with_serpapi(
            query=query,
            max_results=settings.DIGIN_MAX_RESULTS,
        )
        all_search_results.extend(results_for_query)

    cleaned_pages = await _fetch_and_clean_pages(all_search_results)
    summeries = await _summarize_pages(cleaned_pages)
    report = await _synthesize_report(user_query, summeries)
    formatted_report = _format_report(report)

    await update.message.reply_text(formatted_report)
