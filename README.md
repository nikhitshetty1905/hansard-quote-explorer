# Hansard Quote Explorer (1900-1930)

An interactive web application for exploring UK Parliamentary debates on immigration and labour from 1900-1930.

## Features

- **Advanced Framing System**: Quotes are classified into frames (LABOUR_NEED, LABOUR_THREAT, RACIALISED, MIXED, OTHER) using linkage patterns and confidence scoring
- **Historical Analysis**: AI-generated historian analysis of each quote's argumentative structure
- **Clean Interface**: White background, SF Pro fonts, optimized for academic research
- **Quality Filtering**: Only displays high-confidence quotes (5+ out of 10) with clear immigration↔labour connections
- **Enhanced Speaker Identification**: Improved parsing of parliamentary speaker names

## Database

Contains **430+ quotes** from UK Parliamentary debates (1900-1930) where immigration and labour terms co-occur within 40 words, including:

- Complete coverage of major immigration legislation periods
- Post-war reconstruction debates (1919-1920)
- Economic crisis periods
- War-time labour discussions

## Frame Classification

Quotes are classified using enhanced patterns that detect:
- **Linkage patterns**: Causal/contrast connections between immigration and labour
- **Confidence scoring**: Based on term density, proximity, claim verbs, policy terms
- **Academic guards**: Filters procedural noise, hedge words, false positives

## Usage

The interface allows filtering by:
- Year range (1900-1930)
- Frame type
- Automatic quality filtering (confidence ≥ 5)

Results are ordered by confidence score to prioritize the highest-quality quotes.

## Technical Details

- **Data Source**: UK Parliament Historic Hansard API
- **Framework**: Streamlit web application
- **Database**: SQLite with 430+ processed quotes
- **Analysis**: Evidence-based historian system with no hallucination

---

*Academic research tool for studying immigration and labour debates in early 20th century UK Parliament*