"""
Standard benchmark seed data for Chinese A-share markets.

This module defines standard benchmark indices used for fund performance
comparison. These are the primary benchmarks for calculating Information
Ratio, tracking error, and up/down capture ratios.

Critical infrastructure: These seed definitions ensure the system has
appropriate benchmarks for all fund categories from day one.
"""

from __future__ import annotations

import logging
from datetime import date

from app.benchmark.models import BenchmarkIndex
from app.benchmark.repository import BenchmarkRepository
from app.db import get_adapter

logger = logging.getLogger(__name__)

# Standard benchmark indices for Chinese A-share markets
STANDARD_BENCHMARKS = [
    # ===== BROAD MARKET INDICES =====
    {
        "index_code": "000300.SH",
        "index_name": "沪深300",
        "index_type": "broad",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 300,
        "suitable_for_categories": ["宽基", "混合", "股票多空", "灵活配置"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "沪深300指数由上海和深圳证券市场中市值大、流动性好的300只股票组成，综合反映中国A股市场整体表现。"
    },
    {
        "index_code": "000905.SH",
        "index_name": "中证500",
        "index_type": "broad",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 500,
        "suitable_for_categories": ["中盘", "宽基", "混合"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证500指数由全部A股中剔除沪深300指数成分股及总市值排名前300名的股票后，总市值排名靠前的500只股票组成，反映A股市场中等市值公司的整体表现。"
    },
    {
        "index_code": "399406.SZ",
        "index_name": "中证1000",
        "index_type": "broad",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 1000,
        "suitable_for_categories": ["小盘", "宽基"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证1000指数由中证800指数样本股之外规模偏小且流动性好的1000只股票组成，反映A股市场小市值公司的整体表现。"
    },
    {
        "index_code": "000001.SH",
        "index_name": "上证综指",
        "index_type": "broad",
        "market": "SH",
        "base_date": date(1990, 12, 19),
        "base_value": 100,
        "constituents_count": 0,  # All SH stocks
        "suitable_for_categories": ["宽基", "混合"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "上证综合指数反映上海证券交易所上市股票价格表现的总体情况，是反映上海股市整体走势的重要指标。"
    },
    {
        "index_code": "399001.SZ",
        "index_name": "深证成指",
        "index_type": "broad",
        "market": "SZ",
        "base_date": date(1994, 7, 20),
        "base_value": 1000,
        "constituents_count": 500,
        "suitable_for_categories": ["宽基", "混合"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "深证成份指数按一定标准选出500家有代表性的上市公司作为样本股，反映深圳证券市场的整体运行情况。"
    },
    {
        "index_code": "000919.SH",
        "index_name": "中证100",
        "index_type": "broad",
        "market": "CSI",
        "base_date": date(2005, 12, 30),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["大盘", "宽基"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证100指数由沪深300指数成份股中规模最大的100只股票组成，反映A股市场大市值公司的整体表现。"
    },

    # ===== SECTOR INDICES =====
    {
        "index_code": "399006.SZ",
        "index_name": "中证科技",
        "index_type": "sector",
        "market": "CSI",
        "base_date": date(2014, 12, 31),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["科技", "半导体", "人工智能", "电子", "计算机", "通信"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证科技龙头指数选取沪深两市中电子、计算机、通信、生物科技等科技领域中规模大、市占率高的龙头公司股票，反映科技龙头公司的整体表现。"
    },
    {
        "index_code": "399412.SZ",
        "index_name": "中证新能源",
        "index_type": "sector",
        "market": "CSI",
        "base_date": date(2014, 12, 31),
        "base_value": 1000,
        "constituents_count": 80,
        "suitable_for_categories": ["新能源", "光伏", "储能", "电池", "风电"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证新能源指数反映沪深市场中新能源产业上市公司的整体表现，涵盖光伏、风电、储能、新能源汽车等细分领域。"
    },
    {
        "index_code": "399911.SZ",
        "index_name": "中证医药",
        "index_type": "sector",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["医药", "医疗", "生物科技", "健康"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证医药卫生指数反映沪深市场医药卫生行业上市公司的整体表现，涵盖化学制药、中药、生物制品、医疗器械等细分领域。"
    },
    {
        "index_code": "399932.SZ",
        "index_name": "中证消费",
        "index_type": "sector",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["消费", "食品饮料", "家电", "零售"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证主要消费指数反映沪深市场主要消费行业上市公司的整体表现，涵盖食品饮料、家用电器、纺织服装等细分领域。"
    },
    {
        "index_code": "399975.SZ",
        "index_name": "中证金融",
        "index_type": "sector",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["金融", "银行", "证券", "保险"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证800金融指数反映沪深市场金融行业上市公司的整体表现，涵盖银行、证券、保险等细分领域。"
    },

    # ===== STYLE INDICES =====
    {
        "index_code": "399932.SZ",
        "index_name": "中证价值",
        "index_type": "style",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["价值", "红利"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证价值指数选取沪深市场中估值较低、盈利稳定的上市公司股票，反映价值风格股票的整体表现。"
    },
    {
        "index_code": "399911.SZ",
        "index_name": "中证成长",
        "index_type": "style",
        "market": "CSI",
        "base_date": date(2004, 12, 31),
        "base_value": 1000,
        "constituents_count": 100,
        "suitable_for_categories": ["成长", "高增长"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中证成长指数选取沪深市场中营收增长较快、盈利能力较强的上市公司股票，反映成长风格股票的整体表现。"
    },

    # ===== BOND INDICES =====
    {
        "index_code": "CBA00101.CS",
        "index_name": "中债综合财富指数",
        "index_type": "bond",
        "market": "CIC",
        "base_date": date(2001, 12, 31),
        "base_value": 100,
        "constituents_count": 0,
        "suitable_for_categories": ["债券", "货币", "固收"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中债综合财富指数是反映中国人民币债券市场价格走势和投资回报的综合性指数，涵盖国债、金融债、企业债等主要债券品种。"
    },
    {
        "index_code": "CBA00151.CS",
        "index_name": "中债国债总财富指数",
        "index_type": "bond",
        "market": "CIC",
        "base_date": date(2001, 12, 31),
        "base_value": 100,
        "constituents_count": 0,
        "suitable_for_categories": ["国债", "债券"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中债国债总财富指数反映中国国债市场价格走势和投资回报，是衡量国债市场表现的重要指标。"
    },
    {
        "index_code": "CBA00201.CS",
        "index_name": "中债企业债总财富指数",
        "index_type": "bond",
        "market": "CIC",
        "base_date": date(2001, 12, 31),
        "base_value": 100,
        "constituents_count": 0,
        "suitable_for_categories": ["企业债", "信用债", "债券"],
        "data_source": "akshare",
        "update_frequency": "daily",
        "description": "中债企业债总财富指数反映中国企业债市场价格走势和投资回报，涵盖各类企业发行的债券。"
    },
]


def seed_benchmark_database(adapter: any = None) -> dict[str, any]:
    """
    Seed standard benchmark indices into the database.

    This function inserts standard benchmark definitions into the database,
    ensuring the system has appropriate benchmarks for all fund categories.

    Args:
        adapter: Optional database adapter. If None, uses get_adapter()

    Returns:
        Dictionary with statistics:
        {
            'benchmarks_inserted': int,
            'errors': list[str]
        }

    Examples:
        >>> result = seed_benchmark_database()
        >>> print(f"Inserted {result['benchmarks_inserted']} benchmarks")
    """
    if adapter is None:
        adapter = get_adapter()

    logger.info("Seeding benchmark database with standard indices")

    repo = BenchmarkRepository(adapter)
    stats = {
        'benchmarks_inserted': 0,
        'errors': []
    }

    for benchmark_data in STANDARD_BENCHMARKS:
        try:
            # Create BenchmarkIndex model
            benchmark = BenchmarkIndex(**benchmark_data)

            # Insert into database
            success = repo.insert_benchmark(benchmark)

            if success:
                stats['benchmarks_inserted'] += 1
                logger.debug(f"Inserted benchmark {benchmark.index_code}")
            else:
                error_msg = f"Failed to insert {benchmark.index_code}"
                stats['errors'].append(error_msg)
                logger.warning(error_msg)

        except Exception as e:
            error_msg = f"Error inserting {benchmark_data.get('index_code', 'unknown')}: {e}"
            stats['errors'].append(error_msg)
            logger.error(error_msg)

    logger.info(
        f"Benchmark seeding completed: {stats['benchmarks_inserted']} inserted, "
        f"{len(stats['errors'])} errors"
    )

    return stats


def get_benchmark_mapping() -> dict[str, dict[str, str]]:
    """
    Get fund category to benchmark mapping.

    Returns a dictionary mapping fund categories to appropriate benchmarks.

    Returns:
        Dictionary with structure:
        {
            'fund_category': {
                'primary': 'benchmark_code',
                'fallback': ['fallback_code1', 'fallback_code2']
            }
        }

    Examples:
        >>> mapping = get_benchmark_mapping()
        >>> print(mapping['科技']['primary'])
        '399006.SZ'
    """
    return {
        '宽基': {
            'primary': '000300.SH',  # CSI 300
            'fallback': ['000905.SH', '399001.SZ']
        },
        '中盘': {
            'primary': '000905.SH',  # CSI 500
            'fallback': ['000300.SH', '399406.SZ']
        },
        '小盘': {
            'primary': '399406.SZ',  # CSI 1000
            'fallback': ['000905.SH']
        },
        '科技': {
            'primary': '399006.SZ',  # CSI Tech
            'fallback': ['000300.SH']
        },
        '半导体': {
            'primary': '399006.SZ',  # CSI Tech
            'fallback': ['000300.SH']
        },
        '新能源': {
            'primary': '399412.SZ',  # CSI New Energy
            'fallback': ['000300.SH']
        },
        '医药': {
            'primary': '399911.SZ',  # CSI Healthcare
            'fallback': ['000300.SH']
        },
        '消费': {
            'primary': '399932.SZ',  # CSI Consumer
            'fallback': ['000300.SH']
        },
        '金融': {
            'primary': '399975.SZ',  # CSI Financial
            'fallback': ['000300.SH']
        },
        '债券': {
            'primary': 'CBA00101.CS',  # China Bond Composite
            'fallback': ['CBA00151.CS']
        },
        '货币': {
            'primary': 'CBA00101.CS',  # China Bond Composite
            'fallback': []
        },
        '混合': {
            'primary': '000300.SH',  # CSI 300
            'fallback': ['000905.SH']
        },
        '灵活配置': {
            'primary': '000300.SH',  # CSI 300
            'fallback': ['000905.SH']
        },
        '价值': {
            'primary': '399932.SZ',  # CSI Value
            'fallback': ['000300.SH']
        },
        '成长': {
            'primary': '399911.SZ',  # CSI Growth
            'fallback': ['000300.SH']
        },
    }


def get_benchmark_for_category(fund_category: str) -> str:
    """
    Get appropriate benchmark code for a fund category.

    Args:
        fund_category: Fund category name

    Returns:
        Benchmark index code

    Examples:
        >>> get_benchmark_for_category('科技')
        '399006.SZ'
    """
    mapping = get_benchmark_mapping()

    if fund_category in mapping:
        return mapping[fund_category]['primary']
    else:
        # Default to CSI 300
        logger.warning(f"Unknown fund category {fund_category}, using CSI 300")
        return '000300.SH'
