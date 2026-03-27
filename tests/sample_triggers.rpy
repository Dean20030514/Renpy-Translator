# 用于触发各 warning/error 的原文：与 sample_triggers_trans.rpy 逐行配对做 validate_translation
# 行号与下方注释对应，便于构造 trans 文件（注释“行 N”指本组对话所在行号）
label start:
    # 行 5: 长句，用于 W430 过短/过长 边界（原文需 >=20 字）
    e "This is a fairly long English dialogue line with more than twenty characters here."
    # 行 7: 用于 W440（译文含模型套话）
    e "She said something to him."
    # 行 9: 用于 W441（译文含 。. 或 ？?）
    e "Really?"
    # 行 11: 长句，用于 W442（译文>=10 字且中文<10%）
    e "Another long sentence that has at least fifteen characters for the check."
    # 行 13: 用于 W251（占位符顺序不同但集合相同）
    e "First [var_a] and then [var_b] in the dialogue."
    # 行 15: 含锁定术语 MyGame，译文未用「我的游戏」则 E411
    e "Welcome to MyGame, have fun."
    # 行 17: 含禁翻片段 DONT_TRANSLATE_ME，译文缺失或改掉则 E420
    e "Please keep DONT_TRANSLATE_ME as is in the output."
    # 行 19: 含禁翻 v1.0，用于 E420 大小写不敏感（译文保留 v1.0 或 V1.0 皆可）
    e "Version is v1.0 released today."
