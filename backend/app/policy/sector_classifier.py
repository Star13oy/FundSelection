"""
Fund sector classification for policy analysis.

This module classifies funds into policy-relevant sectors based on their names
and categories. This classification enables proper policy scoring by mapping
funds to the sectors affected by government policies.
"""

from __future__ import annotations

import logging
from typing import Final

logger = logging.getLogger(__name__)

# Sector keyword mappings
SECTOR_KEYWORDS: Final[dict[str, list[str]]] = {
    "半导体": ["半导体", "芯片", "集成电路", "存储", "模拟", "射频", "功率"],
    "新能源": ["光伏", "风电", "储能", "电池", "新能源", "锂电", "氢能", "核电"],
    "医药": ["医药", "生物", "医疗", "健康", "创新药", "医疗器械", "疫苗", "中药"],
    "消费": ["消费", "白酒", "食品", "零售", "家电", "餐饮", "旅游", "酒店"],
    "军工": ["军工", "国防", "航空", "航天", "兵器", "船舶"],
    "金融": ["证券", "银行", "保险", "金融", "券商", "信托"],
    "科技": ["科技", "软件", "互联网", "计算机", "云计算", "大数据", "人工智能", "AI", "5G", "通信"],
    "周期": ["煤炭", "石油", "化工", "钢铁", "有色", "建材", "建筑"],
    "地产": ["地产", "房地产", "物业"],
    "汽车": ["汽车", "智能车", "新能源车", "整车"],
    "电力": ["电力", "电网", "发电", "输电"],
    "交通运输": ["交通", "运输", "物流", "港口", "机场", "航空", "快递"],
}

# Broad category mappings
BROAD_CATEGORY_SECTORS: Final[dict[str, str]] = {
    "宽基": "宽基",
    "债券": "债券",
    "混合": "混合",
    "货币": "货币",
    "QDII": "QDII",
    "FOF": "FOF",
}

# Default sector for unclassified funds
DEFAULT_SECTOR = "其他"


def classify_fund_sector(fund_name: str, fund_category: str) -> str:
    """
    Classify a fund into a policy sector.

    Uses keyword matching and category mapping to determine which policy
    sector a fund belongs to. This enables proper policy scoring.

    Args:
        fund_name: Fund name (e.g., "半导体ETF", "沪深300ETF")
        fund_category: Fund category (e.g., "行业", "宽基", "债券")

    Returns:
        Sector name (e.g., "半导体", "新能源", "宽基", "其他")

    Examples:
        >>> classify_fund_sector("半导体ETF", "行业")
        '半导体'
        >>> classify_fund_sector("沪深300ETF", "宽基")
        '宽基'
        >>> classify_fund_sector("消费主题基金", "行业")
        '消费'
        >>> classify_fund_sector("中证500增强", "宽基")
        '宽基'
    """
    # Check broad categories first
    if fund_category in BROAD_CATEGORY_SECTORS:
        return BROAD_CATEGORY_SECTORS[fund_category]

    # Search for sector keywords in fund name
    search_text = fund_name.lower()

    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in search_text:
                logger.debug(f"Classified '{fund_name}' as '{sector}' (matched keyword: {keyword})")
                return sector

    # Default to "其他" if no match found
    logger.debug(f"Could not classify '{fund_name}' (category: {fund_category}), using default")
    return DEFAULT_SECTOR


def get_sector_keywords(sector: str) -> list[str]:
    """
    Get keywords for a given sector.

    Args:
        sector: Sector name

    Returns:
        List of keywords associated with the sector
    """
    return SECTOR_KEYWORDS.get(sector, [])


def is_sector_fund(fund_name: str, fund_category: str, sector: str) -> bool:
    """
    Check if a fund belongs to a specific sector.

    Args:
        fund_name: Fund name
        fund_category: Fund category
        sector: Sector to check

    Returns:
        True if fund belongs to the sector, False otherwise
    """
    return classify_fund_sector(fund_name, fund_category) == sector


def get_all_sectors() -> list[str]:
    """
    Get all defined sector names.

    Returns:
        List of sector names
    """
    return list(SECTOR_KEYWORDS.keys()) + list(BROAD_CATEGORY_SECTORS.values()) + [DEFAULT_SECTOR]


def is_policy_relevant_sector(sector: str) -> bool:
    """
    Check if a sector is relevant for policy analysis.

    Broad categories like "宽基", "债券", "混合" are less sensitive to
    specific sector policies, so they return False.

    Args:
        sector: Sector name

    Returns:
        True if sector is policy-relevant, False otherwise
    """
    return sector in SECTOR_KEYWORDS
