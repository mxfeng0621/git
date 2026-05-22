"""任务定义"""

from core.quest import QuestDef, QuestObjective, QuestReward, QuestType

ALL_QUESTS: list[QuestDef] = [
    # ================================================================
    # 主线任务
    # ================================================================
    QuestDef(
        quest_id="q_goblin_threat",
        name="地精之患",
        description=(
            "镇长艾德温委托你调查并清除幽暗森林中的地精营地。\n"
            "据逃回来的商人说，地精头领比普通地精大得多，也更加凶残。"
        ),
        quest_type=QuestType.MAIN,
        objectives=[
            QuestObjective(
                objective_id="kill_chief", description="击败地精头领",
                target_type="kill", target_id="goblin_chief", target_count=1,
            ),
        ],
        reward=QuestReward(xp=300, gold=200, items=[
            {"item_id": "steel_blade", "quantity": 1},
        ]),
        level_required=1,
        giver_npc="mayor_river",
        completion_text=(
            "你提着地精头领的武器回到河畔镇，镇长艾德温亲自在镇口迎接。\n"
            "「勇士！你是河畔镇的英雄！赏金已经准备好了——\n"
            "不过根据你带回来的情报，地精背后似乎有更强大的势力……\n"
            "恐怕这只是一个开始。等你准备好了，再来找我。」"
        ),
    ),

    # ================================================================
    # 支线任务
    # ================================================================
    QuestDef(
        quest_id="q_elf_ruins",
        name="精灵遗迹",
        description=(
            "酒馆老板娘提到森林西边有一处古老的精灵遗迹，\n"
            "里面据说藏有魔法宝物。去探索一下吧。"
        ),
        quest_type=QuestType.SIDE,
        objectives=[
            QuestObjective(
                objective_id="find_ruins", description="探索精灵遗迹",
                target_type="explore", target_id="elf_ruins", target_count=1,
            ),
        ],
        reward=QuestReward(xp=100, gold=50, items=[
            {"item_id": "mana_potion_m", "quantity": 2},
        ]),
        level_required=1,
        giver_npc="innkeeper",
        completion_text=(
            "你在精灵遗迹中发现了散发着微光的防护戒指，\n"
            "以及在石台下面找到的两瓶法力药水。\n"
            "遗迹中还刻着一段精灵文字：'龙之影将再次笼罩大地'……"
        ),
    ),

    # ================================================================
    # 悬赏任务
    # ================================================================
    QuestDef(
        quest_id="q_wolf_hunt",
        name="猎狼悬赏",
        description=(
            "酒馆布告板上的悬赏令：消灭幽暗森林中威胁旅人的森林狼，\n"
            "每只狼皮10金币。"
        ),
        quest_type=QuestType.BOUNTY,
        objectives=[
            QuestObjective(
                objective_id="kill_wolves", description="消灭森林狼 (0/5)",
                target_type="kill", target_id="wolf", target_count=5,
            ),
        ],
        reward=QuestReward(xp=150, gold=80),
        level_required=1,
        giver_npc="innkeeper",
        completion_text="你凑齐了5张狼皮，酒馆老板娘付了赏金。",
    ),

    # ================================================================
    # 职业任务
    # ================================================================
    QuestDef(
        quest_id="q_warrior_trial",
        name="战士之道",
        description=(
            "铁匠老托克年轻时候也是冒险者。\n"
            "他说如果战士能在不使用治疗药水的情况下击败5个敌人，\n"
            "就赠送一件他珍藏的装备。"
        ),
        quest_type=QuestType.CLASS_QUEST,
        objectives=[
            QuestObjective(
                objective_id="kill_5", description="不使用治疗药水击败5只怪物",
                target_type="kill", target_id="goblin", target_count=5,
            ),
        ],
        reward=QuestReward(xp=200, gold=0, items=[
            {"item_id": "plate_armor", "quantity": 1},
        ]),
        level_required=3,
        giver_npc="blacksmith_tok",
        completion_text=(
            "「好小子！你让我想起了年轻时候的自己。」\n"
            "老托克从箱子底翻出一件擦拭得锃亮的板甲。\n"
            "「这是我当年穿的，现在归你了。」"
        ),
    ),
]
