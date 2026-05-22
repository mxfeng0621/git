"""场景数据定义"""

from dataclasses import dataclass, field


@dataclass
class Scene:
    scene_id: str
    name: str
    description: str
    connections: dict[str, str] = field(default_factory=dict)  # 方向→scene_id
    events: dict[str, dict] = field(default_factory=dict)        # 触发条件→事件
    npcs: list[str] = field(default_factory=list)                # 场景中的NPC id列表
    monster_spawns: list[dict] = field(default_factory=list)
    is_safe: bool = True
    image_hint: str = ""
    interactables: list[dict] = field(default_factory=list)
    # [{label: "推开石门", action: "push", target: "stone_door", icon: "🪨"}]


SCENES: dict[str, Scene] = {
    # ============================================================
    # 序章：河畔镇
    # ============================================================
    "river_town": Scene(
        scene_id="river_town",
        name="河畔镇",
        description=(
            "河畔镇坐落在艾尔德拉大陆的东部边境，是通往外界的重要驿站。\n\n"
            "小镇傍水而建，青石铺就的街道两旁排列着木结构的房屋。\n"
            "镇中心的广场上有一座古老的喷泉，喷泉中央立着早已被岁月侵蚀得面目模糊的石像。\n\n"
            "北方是幽暗森林的入口，据说近来林中地精活动频繁，商旅纷纷绕道而行。\n"
            "东方是通往王国腹地的大道，西方则是连绵的丘陵地带。\n\n"
            "【可前往的地点】\n"
            "· 酒馆 — 「前往 酒馆」 招募同伴、打听消息\n"
            "· 铁匠铺 — 「前往 铁匠铺」 购买武器与装备\n"
            "· 商店 — 「前往 商店」 购买药水与道具\n"
            "· 镇长宅邸 — 「前往 镇长宅邸」 接受任务"
        ),
        connections={
            "北": "dark_forest",
            "酒馆": "river_inn",
            "铁匠铺": "river_smith",
            "商店": "river_shop",
            "镇长宅邸": "river_hall",
        },
        npcs=["mayor_river", "guard_captain"],
        is_safe=True,
        image_hint="a peaceful medieval town by a river, cobblestone streets, wooden houses, fountain in center square, fantasy art style",
        interactables=[
            {"label": "搜索喷泉", "action": "explore", "icon": "🔍"},
            {"label": "查看布告板", "action": "look", "target": "布告板", "icon": "📋"},
            {"label": "休息", "action": "rest", "icon": "🛌"},
        ],
    ),

    "river_inn": Scene(
        scene_id="river_inn",
        name="河畔酒馆",
        description=(
            "「醉龙酒馆」的木招牌在微风中轻轻摇晃。推开厚重的橡木门，\n"
            "温暖的炉火气息混合着麦酒的香味扑面而来。\n\n"
            "酒馆角落里有几个冒险者模样的人正在低声交谈，\n"
            "布告板钉着几张泛黄的悬赏令。\n\n"
            "吧台后面的老板娘朝你点点头，擦拭着一只锡酒杯。\n"
            "旁边坐着一个身着长袍的神秘旅人，用兜帽遮住了大半张脸。"
        ),
        connections={"离开": "river_town"},
        npcs=["innkeeper", "mysterious_stranger"],
        is_safe=True,
        image_hint="cozy medieval tavern interior, fireplace, wooden bar, adventurers at tables, warm atmosphere, fantasy art",
    ),

    "river_smith": Scene(
        scene_id="river_smith",
        name="铁匠铺",
        description=(
            "铁锤敲击铁砧的叮当声在你靠近铁匠铺时越来越清晰。\n"
            "炉火将整个铺子映成橙红色，空气中弥漫着煤炭和热金属的味道。\n\n"
            "墙上挂满了各式武器与防具——长剑、战斧、锁子甲、铁盾，\n"
            "每一件都透着结实耐用的气息。\n\n"
            "铁匠老托克停下手中的活儿，用围裙擦了擦满是老茧的手：\n"
            "「随便看看，都是好货。」"
        ),
        connections={"离开": "river_town"},
        npcs=["blacksmith_tok"],
        is_safe=True,
        image_hint="medieval blacksmith shop, forge fire glowing orange, weapons and armor on walls, burly smith at anvil, fantasy art",
    ),

    "river_shop": Scene(
        scene_id="river_shop",
        name="杂货商店",
        description=(
            "这家不起眼的小店里塞满了各种稀奇古怪的玩意儿——\n"
            "货架上摆着五颜六色的药水、卷轴、投掷武器和冒险必需品。\n\n"
            "瘦高的店主从眼镜上方打量着你：\n"
            "「冒险者？我这儿的货比铁匠铺便宜，当然——质量嘛，你懂的。」"
        ),
        connections={"离开": "river_town"},
        npcs=["shopkeeper_reed"],
        is_safe=True,
        image_hint="crowded medieval general store, shelves with colorful potions and scrolls, thin shopkeeper behind counter, fantasy art",
    ),

    "river_hall": Scene(
        scene_id="river_hall",
        name="镇长宅邸",
        description=(
            "镇长宅邸是河畔镇最大的石造建筑，门前站着两名身着锁子甲、手持长戟的卫兵。\n"
            "他们看到你后微微点头，让开了道路。\n\n"
            "大厅内，头发花白的镇长正盯着墙上的一幅大陆地图出神。\n"
            "听到脚步声，他转过身来，眼神中带着一丝忧虑。\n\n"
            "「冒险者，你来得正好。镇子正面临严重的威胁——\n"
            "北边森林里的地精不知为何变得异常猖獗，已经有好几支商队遇袭了。」"
        ),
        connections={"离开": "river_town"},
        npcs=["mayor_river"],
        is_safe=True,
        image_hint="stone town hall interior, elderly mayor by a large map, guards at entrance, worried expression, fantasy art",
    ),

    # ============================================================
    # 第一章：幽暗森林
    # ============================================================
    "dark_forest": Scene(
        scene_id="dark_forest",
        name="幽暗森林",
        description=(
            "浓密的树冠几乎遮蔽了所有阳光，只有零星的光斑洒在潮湿的林地上。\n"
            "空气中弥漫着苔藓和腐叶的气味，偶尔能听见不知名生物的低吟。\n\n"
            "一条羊肠小道蜿蜒向北，两旁是纠结的树根和长满青苔的巨石。\n"
            "地上散落着破损的货车残骸——看来上一支商队在这里遭遇了不幸。\n\n"
            "南方是返回河畔镇的路。一条隐约的小径岔向西北方向，那边似乎有什么发光的东西。"
        ),
        connections={
            "南": "river_town",
            "北": "forest_deep",
            "西北": "elf_ruins",
        },
        npcs=[],
        monster_spawns=[
            {"enemy_ids": ["goblin"], "chance": 40, "min_count": 1, "max_count": 3},
            {"enemy_ids": ["wolf"], "chance": 20, "min_count": 1, "max_count": 2},
        ],
        is_safe=False,
        image_hint="dark dense forest, barely any sunlight through canopy, moss-covered trees, broken wagon on path, eerie atmosphere, fantasy art",
        interactables=[
            {"label": "搜索残骸", "action": "explore", "icon": "🔍"},
            {"label": "检查破旧马车", "action": "look", "target": "破旧马车", "icon": "👀"},
        ],
    ),

    "forest_deep": Scene(
        scene_id="forest_deep",
        name="森林深处",
        description=(
            "这里的树木更加古老粗壮，树干上刻着模糊不清的符文，\n"
            "似乎是不知多少年前留下的。林间的空气变得沉重，带着一丝魔法残留的气息。\n\n"
            "前方出现了一片空地，中央堆砌着粗糙的木栅栏和兽皮帐篷——\n"
            "毫无疑问，这就是地精的营地。火堆旁的地精守卫正用凶狠的小眼睛四处张望。\n\n"
            "【警告：前方为地精营地，进入将触发Boss战】"
        ),
        connections={
            "南": "dark_forest",
            "进入营地": "goblin_camp",
        },
        npcs=[],
        monster_spawns=[
            {"enemy_ids": ["goblin", "goblin_archer"], "chance": 50, "min_count": 2, "max_count": 4},
        ],
        is_safe=False,
        image_hint="ancient forest with rune-carved trees, goblin camp ahead with wooden palisade and hide tents, campfire, fantasy art",
    ),

    "goblin_camp": Scene(
        scene_id="goblin_camp",
        name="地精营地",
        description=(
            "营地里一片狼藉，兽皮帐篷歪歪扭扭，地上散落着被啃过的骨\n"
            "和被掠夺的货物。营地最深处，一只体型硕大的地精头领正坐在宝座上——\n"
            "所谓的宝座，不过是几口倒扣的铁锅和一块破旧的地毯。\n\n"
            "【Boss战：地精头领】击败后可获得丰厚奖励。"
        ),
        connections={"离开": "forest_deep"},
        npcs=[],
        is_safe=False,
        events={
            "on_enter": {"type": "combat", "enemy_ids": ["goblin_chief", "goblin", "goblin"]},
            "on_victory": {
                "type": "reward",
                "gold": 50,
                "items": [{"item_id": "steel_blade", "chance": 60}],
                "set_flag": "goblin_camp_cleared",
            },
        },
        image_hint="goblin camp interior, messy tents, looted goods scattered, goblin chief on makeshift throne, fantasy art",
    ),

    "elf_ruins": Scene(
        scene_id="elf_ruins",
        name="精灵遗迹",
        description=(
            "断壁残垣间爬满了发光藤蔓，散发出柔和的蓝白色光芒——\n"
            "这就是你从远处看到的光源。残存的石柱上镌刻着精致的精灵文字，\n"
            "虽然经历了数百年风雨，依然透着优雅的气息。\n\n"
            "遗迹中央有一座半倾的石台，上面放着一枚散发着微光的戒指。\n"
            "【输入「拾取 戒指」可获得防护戒指】"
        ),
        connections={"东南": "dark_forest"},
        npcs=[],
        is_safe=True,
        events={
            "on_search": {
                "type": "loot",
                "items": [{"item_id": "ring_of_protection", "chance": 100}],
                "once": True,
            },
        },
        image_hint="ancient elven ruins in forest, glowing blue vines on broken pillars, stone altar with glowing ring, magical atmosphere, fantasy art",
    ),

    # ============================================================
    # 第二章：废弃矿洞（入口）
    # ============================================================
    "abandoned_mine": Scene(
        scene_id="abandoned_mine",
        name="废弃矿洞",
        description=(
            "矿洞入口被粗壮的木梁支撑着，洞口吹出一股阴冷潮湿的风。\n"
            "一块褪色的木牌歪斜地插在入口旁，上面写着：\n"
            "「莫格瑞姆矿业——闲人免入」。\n\n"
            "洞口附近的地面上散落着生锈的矿镐和破碎的矿石。\n"
            "仔细听，洞内似乎有什么动静……\n\n"
            "【推荐等级 6+，内容待后续版本开放】"
        ),
        connections={"南": "dark_forest"},
        npcs=[],
        is_safe=False,
        monster_spawns=[
            {"enemy_ids": ["skeleton", "giant_spider"], "chance": 35, "min_count": 1, "max_count": 3},
        ],
        image_hint="abandoned mine entrance in hillside, wooden supports, warning sign, rusty pickaxes on ground, dark and foreboding, fantasy art",
    ),
}
