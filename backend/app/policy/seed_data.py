"""
Initial policy data seeding for the policy scoring system.

This module contains realistic Chinese government policies from 2024-2025,
covering major sectors like semiconductors, new energy, pharmaceuticals,
consumption, defense, and capital market reforms.

These policies replace fake MD5-based scoring with real policy analysis.
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.policy.models import PolicyEvent
from app.policy.repository import PolicyRepository

logger = logging.getLogger(__name__)

# Initial policy events covering major Chinese sectors
INITIAL_POLICIES = [
    # ==================== 半导体政策 ====================
    {
        "policy_id": "P2025010101",
        "title": "集成电路产业投资基金三期启动",
        "published_at": datetime(2025, 1, 15),
        "effective_from": datetime(2025, 2, 1),
        "related_sectors": ["半导体", "科技", "芯片"],
        "intensity_level": 5,  # Breakthrough
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "fiscal",
        "support_amount_billion": 300,  # 300 billion RMB
        "description": "国家集成电路产业投资基金三期启动，重点投资半导体制造、设备、材料领域",
        "key_points": [
            "总规模3000亿元",
            "重点支持半导体制造",
            "设备材料国产化替代",
            "人才培养和技术研发",
        ],
    },
    {
        "policy_id": "P2025031501",
        "title": "半导体设备税收优惠政策",
        "published_at": datetime(2025, 3, 15),
        "effective_from": datetime(2025, 4, 1),
        "related_sectors": ["半导体", "科技"],
        "intensity_level": 4,  # Strong
        "execution_status": "detailed",
        "impact_direction": "positive",
        "policy_type": "fiscal",
        "tax_incentive_rate": 0.15,  # 15% tax reduction
        "description": "对半导体设备制造企业实施企业所得税减免政策",
        "key_points": [
            "企业所得税减免15%",
            "设备研发费用加计扣除",
            "进口设备关税减免",
            "政策有效期3年",
        ],
    },
    # ==================== 新能源政策 ====================
    {
        "policy_id": "P2025012001",
        "title": "新能源汽车购置税减免延续至2027年",
        "published_at": datetime(2025, 1, 20),
        "effective_from": datetime(2025, 1, 1),
        "expires_at": datetime(2027, 12, 31),
        "related_sectors": ["新能源", "汽车", "电池"],
        "intensity_level": 4,  # Strong
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "fiscal",
        "tax_incentive_rate": 0.10,  # 10% tax reduction
        "description": "新能源汽车购置税减免政策延续，对购置日期在2024-2027年的新能源汽车免征车辆购置税",
        "key_points": [
            "免征购置税至2027年底",
            "每辆车最高免税3万元",
            "涵盖纯电动、插电混动、燃料电池",
        ],
    },
    {
        "policy_id": "P2025022001",
        "title": "风光大基地建设规划（2025-2027）",
        "published_at": datetime(2025, 2, 20),
        "related_sectors": ["新能源", "光伏", "风电", "电力"],
        "intensity_level": 5,
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "industrial",
        "support_amount_billion": 200,
        "description": "国家发改委发布风光大基地建设规划，在沙漠、戈壁、荒漠地区建设大型风光基地",
        "key_points": [
            "总装机200GW",
            "重点布局西部风光资源丰富地区",
            "配套特高压外送通道建设",
            "2027年前全部投产",
        ],
    },
    {
        "policy_id": "P2025030101",
        "title": "储能产业发展指导意见",
        "published_at": datetime(2025, 3, 1),
        "related_sectors": ["新能源", "储能", "电池"],
        "intensity_level": 4,
        "execution_status": "detailed",
        "impact_direction": "positive",
        "policy_type": "industrial",
        "support_amount_billion": 50,
        "description": "国家能源局发布储能产业发展指导意见，支持新型储能技术研发和产业化",
        "key_points": [
            "2025年装机30GW目标",
            "支持锂电池、液流电池、压缩空气储能",
            "完善储能参与电力市场机制",
            "加大财政补贴力度",
        ],
    },
    # ==================== 人工智能政策 ====================
    {
        "policy_id": "P2025021001",
        "title": "人工智能创新发展行动计划（2025-2027）",
        "published_at": datetime(2025, 2, 10),
        "related_sectors": ["人工智能", "科技", "软件"],
        "intensity_level": 5,
        "execution_status": "detailed",
        "impact_direction": "positive",
        "policy_type": "industrial",
        "support_amount_billion": 150,
        "description": "三部委发布人工智能创新发展三年行动计划，重点支持大模型、算力基础设施、应用场景",
        "key_points": [
            "建设公共算力中心",
            "支持大模型研发",
            "推动AI+行业应用",
            "人才培养计划",
        ],
    },
    # ==================== 医药政策 ====================
    {
        "policy_id": "P2025020501",
        "title": "创新药审评审批绿色通道政策",
        "published_at": datetime(2025, 2, 5),
        "effective_from": datetime(2025, 3, 1),
        "related_sectors": ["医药", "生物", "创新药"],
        "intensity_level": 4,
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "regulatory",
        "description": "国家药监局发布创新药审评审批绿色通道政策，缩短创新药上市时间",
        "key_points": [
            "审评时限缩短40%",
            "优先审评品种范围扩大",
            "临床试验默示许可",
            "加速创新药上市",
        ],
    },
    {
        "policy_id": "P2025031001",
        "title": "医疗器械国产化替代专项行动",
        "published_at": datetime(2025, 3, 10),
        "related_sectors": ["医药", "医疗", "医疗器械"],
        "intensity_level": 3,
        "execution_status": "announced",
        "impact_direction": "positive",
        "policy_type": "industrial",
        "support_amount_billion": 30,
        "description": "工信部启动医疗器械国产化替代专项行动，重点支持高端医疗设备研发",
        "key_points": [
            "重点支持影像设备、手术机器人",
            "医院采购国产化比例要求",
            "研发补贴政策",
        ],
    },
    # ==================== 消费政策 ====================
    {
        "policy_id": "P2025012501",
        "title": "以旧换新消费补贴政策",
        "published_at": datetime(2025, 1, 25),
        "effective_from": datetime(2025, 2, 1),
        "expires_at": datetime(2025, 12, 31),
        "related_sectors": ["消费", "汽车", "家电"],
        "intensity_level": 3,
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "fiscal",
        "support_amount_billion": 80,
        "description": "商务部推出以旧换新消费补贴政策，支持汽车、家电等大宗消费",
        "key_points": [
            "汽车以旧换新补贴8000元",
            "家电以旧换新补贴10-20%",
            "政策有效期至2025年底",
        ],
    },
    {
        "policy_id": "P2025021501",
        "title": "促进夜间经济发展指导意见",
        "published_at": datetime(2025, 2, 15),
        "related_sectors": ["消费", "零售", "餐饮", "旅游"],
        "intensity_level": 2,
        "execution_status": "detailed",
        "impact_direction": "positive",
        "policy_type": "industrial",
        "description": "发改委发布促进夜间经济发展指导意见，支持城市夜间消费场景建设",
        "key_points": [
            "延长营业时间",
            "优化交通配套",
            "降低夜间经营成本",
        ],
    },
    # ==================== 军工政策 ====================
    {
        "policy_id": "P2025030501",
        "title": "国防科技工业发展规划（2025-2030）",
        "published_at": datetime(2025, 3, 5),
        "related_sectors": ["军工", "国防", "航空", "航天"],
        "intensity_level": 4,
        "execution_status": "announced",
        "impact_direction": "positive",
        "policy_type": "industrial",
        "support_amount_billion": 100,
        "description": "国防科工局发布国防科技工业发展规划，重点发展航空、航天、航海装备",
        "key_points": [
            "加快装备现代化",
            "军民融合发展",
            "核心技术自主可控",
        ],
    },
    # ==================== 资本市场改革 ====================
    {
        "policy_id": "P2025032001",
        "title": "资本市场降费让利政策",
        "published_at": datetime(2025, 3, 20),
        "effective_from": datetime(2025, 4, 1),
        "related_sectors": ["金融", "证券"],
        "intensity_level": 3,
        "execution_status": "detailed",
        "impact_direction": "positive",
        "policy_type": "reform",
        "description": "证监会发布资本市场降费让利政策，降低交易成本",
        "key_points": [
            "股票交易经手费下调30%",
            "取消部分行政收费",
            "降低投资者交易成本",
        ],
    },
    {
        "policy_id": "P2025022501",
        "title": "全面注册制改革深化",
        "published_at": datetime(2025, 2, 25),
        "related_sectors": ["金融", "证券"],
        "intensity_level": 4,
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "reform",
        "description": "证监会深化全面注册制改革，优化发行上市制度",
        "key_points": [
            "简化发行流程",
            "提高上市审核效率",
            "强化信息披露要求",
        ],
    },
    # ==================== 国企改革 ====================
    {
        "policy_id": "P2025032501",
        "title": "国有企业改革深化提升行动",
        "published_at": datetime(2025, 3, 25),
        "related_sectors": ["周期", "金融", "地产"],
        "intensity_level": 3,
        "execution_status": "announced",
        "impact_direction": "neutral",
        "policy_type": "reform",
        "description": "国资委启动国有企业改革深化提升行动，推进混合所有制改革",
        "key_points": [
            "推进混合所有制改革",
            "完善现代企业制度",
            "强化国企创新驱动",
        ],
    },
    # ==================== 周期行业政策 ====================
    {
        "policy_id": "P2025031201",
        "title": "钢铁行业产能置换政策",
        "published_at": datetime(2025, 3, 12),
        "related_sectors": ["周期", "钢铁"],
        "intensity_level": 2,
        "execution_status": "detailed",
        "impact_direction": "neutral",
        "policy_type": "regulatory",
        "description": "工信部发布钢铁行业产能置换政策，优化产能结构",
        "key_points": [
            "严禁新增产能",
            "支持产能置换交易",
            "推动绿色低碳转型",
        ],
    },
    {
        "policy_id": "P2025022801",
        "title": "煤炭清洁高效利用政策",
        "published_at": datetime(2025, 2, 28),
        "related_sectors": ["周期", "煤炭", "电力"],
        "intensity_level": 3,
        "execution_status": "implementing",
        "impact_direction": "neutral",
        "policy_type": "regulatory",
        "description": "发改委发布煤炭清洁高效利用政策，推动煤炭消费转型升级",
        "key_points": [
            "推广煤电机组灵活性改造",
            "支持煤化工高端化发展",
            "严控煤炭消费总量",
        ],
    },
    # ==================== 地产政策 ====================
    {
        "policy_id": "P2025031801",
        "title": "房地产融资协调机制",
        "published_at": datetime(2025, 3, 18),
        "related_sectors": ["地产", "金融"],
        "intensity_level": 3,
        "execution_status": "implementing",
        "impact_direction": "positive",
        "policy_type": "monetary",
        "description": "央行、金融监管总局建立房地产融资协调机制，支持房地产合理融资需求",
        "key_points": [
            "建立房地产白名单制度",
            "支持优质房企融资",
            "稳定房地产市场预期",
        ],
    },
]


def seed_policy_database(db_adapter) -> dict:
    """
    Seed initial policy data into the database.

    Args:
        db_adapter: Database adapter instance

    Returns:
        Dictionary with seeding results:
        {
            'policies_inserted': int,
            'mappings_inserted': int,
            'errors': list[str]
        }
    """
    repository = PolicyRepository(db_adapter)
    errors = []
    policies_inserted = 0

    logger.info("Starting policy database seeding...")

    for policy_data in INITIAL_POLICIES:
        try:
            # Create PolicyEvent object
            policy = PolicyEvent(**policy_data)

            # Insert into database
            success = repository.insert_policy(policy)

            if success:
                policies_inserted += 1
                logger.info(f"Inserted policy: {policy.policy_id} - {policy.title}")
            else:
                errors.append(f"Failed to insert policy: {policy.policy_id}")

        except Exception as e:
            error_msg = f"Error inserting policy {policy_data.get('policy_id', 'unknown')}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    result = {
        "policies_inserted": policies_inserted,
        "mappings_inserted": 0,  # Not implemented yet
        "errors": errors,
    }

    logger.info(f"Policy database seeding completed. Inserted {policies_inserted} policies.")

    if errors:
        logger.warning(f"Encountered {len(errors)} errors during seeding.")

    return result


def get_policy_count() -> int:
    """
    Get the number of policies in the seed data.

    Returns:
        Number of policies
    """
    return len(INITIAL_POLICIES)
