"""
民航专业术语库
"""

import re
from typing import Dict, List, Tuple


class AviationTermsProcessor:
    """民航术语处理器"""
    
    def __init__(self):
        # 口语化到规范化的映射
        self.term_mapping = {
            # 基础术语
            "飞机": "航空器",
            "客机": "客运航空器", 
            "货机": "货运航空器",
            "机场": "机场",
            "跑道": "跑道",
            "停机坪": "停机坪",
            "塔台": "管制塔台",
            "空管": "空中交通管制",
            
            # 川航相关
            "川航": "四川航空股份有限公司",
            "3U": "四川航空",
            "川航集团": "四川航空集团有限责任公司",
            
            # 职务简称
            "总": "总经理",
            "书记": "党委书记",
            "副总": "副总经理",
            "总工": "总工程师",
            "安全总监": "安全总监",
            "运控": "运行控制",
            "机务": "机务维修",
            "乘务": "客舱服务",
            
            # 部门简称
            "运控中心": "运行控制中心",
            "机务部": "机务维修部",
            "安全部": "安全管理部",
            "飞行部": "飞行部",
            "乘务部": "客舱服务部",
            "地服": "地面服务",
            "货运": "货运服务",
            
            # 业务术语
            "航班": "航班",
            "班期": "航班时刻",
            "时刻": "航班时刻",
            "航线": "航线",
            "航权": "航权",
            "时刻协调": "航班时刻协调",
            "配载": "载重平衡",
            "放行": "航班放行",
            "签派": "飞行签派",
            
            # 安全术语
            "不安全事件": "不安全事件",
            "事故征候": "事故征候",
            "安全检查": "安全检查",
            "安全评估": "安全风险评估",
            "SMS": "安全管理体系",
            "QAR": "快速存取记录器",
            "FOQA": "飞行运行质量保证",
            
            # 维修术语
            "定检": "定期检修",
            "航线维护": "航线维护",
            "大修": "大修理",
            "适航": "适航性",
            "MEL": "最低设备清单",
            "CDL": "构型偏离清单",
            
            # 运行术语
            "备降": "备用着陆",
            "返航": "返回起飞机场",
            "延误": "航班延误",
            "取消": "航班取消",
            "调机": "调机飞行",
            "加班": "加班航班",
            
            # 服务术语
            "头等舱": "头等舱",
            "公务舱": "公务舱", 
            "经济舱": "经济舱",
            "超售": "超售",
            "不正常航班": "不正常航班服务",
            
            # 货运术语
            "货邮": "货物和邮件",
            "腹舱": "客机腹舱",
            "危险品": "危险物品",
            "特殊货物": "特殊货物",
            
            # 财务术语
            "收益": "营业收入",
            "成本": "营业成本",
            "利润": "营业利润",
            "客座率": "客座率",
            "载运率": "载运率",
            "周转量": "运输周转量",
            
            # 管理术语
            "三重一大": "重大事项决策、重要干部任免、重要项目安排、大额资金使用",
            "双控": "安全风险分级管控和隐患排查治理双重预防机制",
            "四不两直": "不发通知、不打招呼、不听汇报、不用陪同接待，直奔基层、直插现场",
            
            # 监管机构
            "民航局": "中国民用航空局",
            "地区管理局": "民航地区管理局",
            "监管局": "民航安全监督管理局",
            "西南局": "民航西南地区管理局",
            "华东局": "民航华东地区管理局",
            
            # 机型简称
            "320": "空客A320",
            "321": "空客A321", 
            "330": "空客A330",
            "350": "空客A350",
            "737": "波音737",
            "787": "波音787",
            "ARJ": "ARJ21",
            "C919": "C919",
        }
        
        # 数字和单位规范化
        self.unit_mapping = {
            "万": "万",
            "亿": "亿",
            "千": "千",
            "百": "百",
            "架": "架",
            "班": "班",
            "人": "人",
            "吨": "吨",
            "公里": "公里",
            "小时": "小时",
            "分钟": "分钟",
            "秒": "秒",
            "米": "米",
            "度": "度",
            "节": "节",
            "英尺": "英尺",
        }
        
        # 常见口语化表达
        self.colloquial_patterns = [
            (r"(\d+)个亿", r"\1亿"),
            (r"(\d+)个万", r"\1万"),
            (r"(\d+)多万", r"\1万余"),
            (r"(\d+)来万", r"\1万余"),
            (r"大概(\d+)", r"约\1"),
            (r"差不多(\d+)", r"约\1"),
            (r"基本上", ""),
            (r"这个那个", ""),
            (r"嗯嗯", ""),
            (r"啊啊", ""),
        ]
    
    def normalize_text(self, text: str) -> str:
        """
        规范化文本
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        result = text
        
        # 1. 处理口语化表达
        for pattern, replacement in self.colloquial_patterns:
            result = re.sub(pattern, replacement, result)
        
        # 2. 替换专业术语
        for colloquial, formal in self.term_mapping.items():
            # 使用词边界匹配，避免部分匹配
            pattern = r'\b' + re.escape(colloquial) + r'\b'
            result = re.sub(pattern, formal, result)
        
        # 3. 清理多余空格
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def extract_aviation_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取民航相关实体
        
        Args:
            text: 文本内容
            
        Returns:
            实体字典
        """
        entities = {
            "departments": [],  # 部门
            "positions": [],    # 职务
            "aircraft_types": [], # 机型
            "airports": [],     # 机场
            "routes": [],       # 航线
            "regulations": [],  # 法规
        }
        
        # 部门识别
        dept_keywords = ["部", "中心", "处", "科", "组", "队"]
        for keyword in dept_keywords:
            pattern = r'[\u4e00-\u9fa5]+' + keyword
            matches = re.findall(pattern, text)
            entities["departments"].extend(matches)
        
        # 职务识别
        position_keywords = ["总经理", "书记", "主任", "经理", "主管", "专员", "员"]
        for pos in position_keywords:
            if pos in text:
                entities["positions"].append(pos)
        
        # 机型识别
        aircraft_pattern = r'[A-Z]\d{3}|ARJ\d+|C\d{3}'
        aircraft_matches = re.findall(aircraft_pattern, text)
        entities["aircraft_types"].extend(aircraft_matches)
        
        # 去重
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def get_formal_term(self, colloquial_term: str) -> str:
        """
        获取规范术语
        
        Args:
            colloquial_term: 口语化术语
            
        Returns:
            规范术语
        """
        return self.term_mapping.get(colloquial_term, colloquial_term)
    
    def add_custom_terms(self, custom_mapping: Dict[str, str]):
        """
        添加自定义术语映射
        
        Args:
            custom_mapping: 自定义映射字典
        """
        self.term_mapping.update(custom_mapping)


# 全局实例
aviation_processor = AviationTermsProcessor()
