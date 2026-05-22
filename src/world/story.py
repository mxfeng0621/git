"""剧情数据 — NPC对话树与剧本触发"""

from core.dialogue import DialogueTree, DialogueNode, DialogueOption

# ---- 镇长 ----
mayor_tree = DialogueTree(
    npc_id="mayor_river", npc_name="镇长艾德温", greeting_node="greeting",
    nodes={
        "greeting": DialogueNode(
            node_id="greeting", speaker="镇长艾德温",
            text="「冒险者，你来得正好。镇子正面临严重的威胁——\n"
                 "北边森林里的地精不知为何变得异常猖獗，已经有好几支商队遇袭了。\n"
                 "我需要一位勇敢的人去调查地精的动向，并消灭他们的头领。」",
            options=[
                DialogueOption("接受任务", next_id="accept_quest",
                               effects={"start_quest": "q_goblin_threat"}),
                DialogueOption("我需要更多信息", next_id="more_info"),
                DialogueOption("我现在还没准备好", next_id="not_ready"),
            ],
        ),
        "accept_quest": DialogueNode(
            node_id="accept_quest", speaker="镇长艾德温",
            text="「很好！这才是艾尔德拉需要的勇士。\n"
                 "地精营地在森林深处，沿着主路向北走就能找到。\n"
                 "不过要小心——据逃回来的商人说，地精的头领比普通地精大得多。\n"
                 "我在镇子里等你的好消息。」",
            options=[
                DialogueOption("我这就出发", next_id=""),
                DialogueOption("有没有赏金？", next_id="reward_info"),
            ],
            on_enter={"affinity": 10},
        ),
        "more_info": DialogueNode(
            node_id="more_info", speaker="镇长艾德温",
            text="「大约从三周前开始，地精的数量突然增多，而且变得有组织起来。\n"
                 "以前它们不过是一盘散沙的小毛贼，现在却敢围攻商队。\n"
                 "我怀疑背后有更强大的势力在操控。不过眼下，先解决营地的头领才是当务之急。」",
            options=[
                DialogueOption("我接下这个任务", next_id="accept_quest",
                               effects={"start_quest": "q_goblin_threat"}),
                DialogueOption("让我再想想", next_id=""),
            ],
        ),
        "not_ready": DialogueNode(
            node_id="not_ready", speaker="镇长艾德温",
            text="「没关系，年轻人。去酒馆招募几个可靠的同伴，\n"
                 "到铁匠铺置办些装备，准备好了再来找我。」",
            options=[DialogueOption("好的", next_id="")],
        ),
        "reward_info": DialogueNode(
            node_id="reward_info", speaker="镇长艾德温",
            text="「赏金自然少不了。消灭地精头领，镇上的金库出200金币。\n"
                 "另外，我在铁匠铺给你准备了一件礼物——算是个人赞助吧，哈！」",
            options=[DialogueOption("成交！", next_id="")],
        ),
    },
)

# ---- 酒馆老板娘 ----
innkeeper_tree = DialogueTree(
    npc_id="innkeeper", npc_name="酒馆老板娘玛莎", greeting_node="greeting",
    nodes={
        "greeting": DialogueNode(
            node_id="greeting", speaker="老板娘玛莎",
            text="「欢迎来到醉龙酒馆！来杯麦酒还是想住一晚？\n"
                 "当然，如果你想招募冒险伙伴，来对地方了——\n"
                 "布告板上有悬赏，角落里总有几个待业的佣兵。」",
            options=[
                DialogueOption("我想招募同伴", next_id="recruit"),
                DialogueOption("有什么消息吗？", next_id="rumors"),
                DialogueOption("来一杯麦酒", next_id="buy_drink"),
                DialogueOption("只是随便看看", next_id=""),
            ],
        ),
        "recruit": DialogueNode(
            node_id="recruit", speaker="老板娘玛莎",
            text="「今天运气不错，还有三位冒险者在这里。\n"
                 "那个穿长袍的神秘旅人是个法师，似乎学识渊博；\n"
                 "角落里安静喝酒的小个子是个身手矫健的盗贼；\n"
                 "还有那边那个矮人牧师，是从北方山区来的，据说医术了得。\n"
                 "想和谁聊聊？就说是我介绍的！」",
            options=[
                DialogueOption("招募法师（梅林加入队伍）", next_id="recruit_mage",
                               effects={"recruit": "merlin"}),
                DialogueOption("招募盗贼（影刃加入队伍）", next_id="recruit_rogue",
                               effects={"recruit": "shade"}),
                DialogueOption("招募牧师（圣光加入队伍）", next_id="recruit_cleric",
                               effects={"recruit": "holy"}),
                DialogueOption("先不了", next_id=""),
            ],
        ),
        "rumors": DialogueNode(
            node_id="rumors", speaker="老板娘玛莎",
            text="「听说北边森林最近不太平。不过也有好消息——\n"
                 "有个猎人在森林西边发现了一处古老的精灵遗迹，\n"
                 "据说里面有值钱的宝贝。当然，真假就不知道咯。」",
            options=[DialogueOption("有意思，谢谢", next_id="")],
        ),
        "buy_drink": DialogueNode(
            node_id="buy_drink", speaker="老板娘玛莎",
            text="「好嘞！5个铜币——哦不，对冒险者免费，第一杯算我的。」\n"
                 "她把一大杯冒着泡沫的麦酒推到你面前。\n「祝你的冒险一切顺利！」",
            options=[DialogueOption("干杯！", next_id="")],
        ),
        "recruit_mage": DialogueNode(
            node_id="recruit_mage", speaker="神秘旅人",
            text="神秘旅人放下兜帽，露出一张清瘦而睿智的面孔。\n"
                 "「我叫梅林，正在寻找一条古龙传说的线索。\n"
                 "如果你也往北边走，我可以与你同行。」\n\n【梅林（精灵法师）已加入队伍】",
            options=[DialogueOption("欢迎加入", next_id="")],
        ),
        "recruit_rogue": DialogueNode(
            node_id="recruit_rogue", speaker="影刃",
            text="小个子放下酒杯，露出一丝狡黠的笑容。\n"
                 "「影刃，大家这么叫我。擅长开锁和背后捅刀子——都是合法技能。\n"
                 "正好欠老板娘一个人情，帮你一次吧。」\n\n【影刃（半身人盗贼）已加入队伍】",
            options=[DialogueOption("合作愉快", next_id="")],
        ),
        "recruit_cleric": DialogueNode(
            node_id="recruit_cleric", speaker="圣光",
            text="矮人牧师放下酒杯，站起来行了个礼。\n"
                 "「我叫圣光，来自北方的群山。圣光指引我南下寻找需要帮助的人。\n"
                 "你的旅途似乎不凡，我愿意与你同行。」\n\n【圣光（矮人牧师）已加入队伍】",
            options=[DialogueOption("荣幸之至", next_id="")],
        ),
    },
)

# ---- 铁匠 ----
blacksmith_tree = DialogueTree(
    npc_id="blacksmith_tok", npc_name="铁匠老托克", greeting_node="greeting",
    nodes={
        "greeting": DialogueNode(
            node_id="greeting", speaker="铁匠老托克",
            text="「嘿，来看看吧。虽然铺子不大，但我打的铁绝对结实。\n"
                 "眼下不太平，武器销路好着呢。你想买点什么？」",
            options=[
                DialogueOption("看看武器", next_id="shop"),
                DialogueOption("我是镇长介绍来的", next_id="mayor_gift",
                               condition="quest_active:q_goblin_threat"),
                DialogueOption("只是看看", next_id=""),
            ],
        ),
        "shop": DialogueNode(
            node_id="shop", speaker="铁匠老托克",
            text="「铁剑30金币，精钢长剑80金币。防具的话——\n"
                 "皮甲20金币，锁子甲60金币，铁头盔15金币。都是实价，不还价。」",
            options=[DialogueOption("好，我考虑一下", next_id="")],
        ),
        "mayor_gift": DialogueNode(
            node_id="mayor_gift", speaker="铁匠老托克",
            text="「哦！镇长打过招呼了。来——这把精钢长剑是他的私人收藏，\n"
                 "现在归你了。好好用它砍几个地精脑袋！」\n\n【获得：精钢长剑】",
            options=[DialogueOption("多谢！", next_id="")],
            on_enter={"give_item": "steel_blade"},
        ),
    },
)

# ---- 杂货店主 ----
shopkeeper_tree = DialogueTree(
    npc_id="shopkeeper_reed", npc_name="杂货店主里德", greeting_node="greeting",
    nodes={
        "greeting": DialogueNode(
            node_id="greeting", speaker="店主里德",
            text="「欢迎光临！药水、卷轴、飞刀——冒险需要的一切，应有尽有。\n"
                 "小治疗药水25金币，中型的60金币。法力药水小的20，中的50。\n"
                 "飞刀5金币一把，丢出去就不还了哦。」",
            options=[
                DialogueOption("看看药水", next_id=""),
                DialogueOption("有没有特价商品？", next_id="discount"),
                DialogueOption("再见", next_id=""),
            ],
        ),
        "discount": DialogueNode(
            node_id="discount", speaker="店主里德",
            text="「特价？哈！这年头连进货都困难。\n"
                 "不过……如果你能搞定北边森林里的地精问题，以后我给你打九折。」",
            options=[DialogueOption("一言为定", next_id="")],
        ),
    },
)

# 注册
ALL_DIALOGUES: dict = {
    "mayor_river": mayor_tree,
    "innkeeper": innkeeper_tree,
    "blacksmith_tok": blacksmith_tree,
    "shopkeeper_reed": shopkeeper_tree,
}
