


label basement2am:
    hide screen locations
    scene black
    $ dtime = 2
    "You wake up."
    pov "{i}Huh? Did I hear something?{/i}"
    pov "{i}No. It was nothing.{/i}"
    "You fall asleep again."
    with vpunch
    pov "{i}DAMN!{/i}"
    " \"Make sure you come here again at night time so that I can teach you more!\" "
    pov "{i}I was right. That noise was [ls].{/i}"
    pov "{i}I must know what they're up to.{/i}"
    "You go to the basement silently."
    if gamemusic == True:
        stop music fadeout 2
        play music "music/NTR.mp3"
    scene basement 2am 001
    pov "{i}What the hell? [ls] is restrained and Davide is going to fuck her.{/i}"
    pov "{i}She's even wearing a ball-gag. Is he raping her?{/i}"
    davide "Now it's the time you get my big black dick, little slut!"
    davide "Are you happy to loose your anal virginity to me?"
    ls "Yesh... Hm... appy."
    pov "{i}Thank god. At least he's not raping her.{/i}"
    pov "{i}But should I show them myself or just watch?{/i}"
    call screen base2amwatch

screen base2amwatch():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 734 ypos 113 action (Hide ('base2amwatch'), Jump('base2show')) hovered tt.Action ("Show yourself") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1334 ypos 113 action (Hide ('base2amwatch'), Jump('base2hide')) hovered tt.Action ("Watch them secretly") focus_mask True


    frame:
        xalign .5
        text tt.value

label base2show:
    pov "{i}I won't hide myself, they should know that I'm aware.{/i}"
    scene basement 2am 002a
    pov "Hey there, lovebirds!"
    ls "Hnng?"
    davide "Oh hey [pov]! You come at the right time, the time she sacrifices her anal virginity to me."
    ls "Hmm!"
    pov "Oh, you aren't so happy that I'm here [ls]?"
    ls "HNNG!"
    davide "Shut up slut! If he want to watch and learn he can do this!"
    scene basement 2am 003a
    ls "Hnn..."
    pov "But why this setup?"
    davide "She needs to be restraint when she feel my big dick for her first time."
    davide "It won't be easy to take for her and I don't need her to struggle like crazy."
    pov "And the ball-gag?"
    davide "What do you think? She'll scream like crazy, haha!"
    pov "Somewhat nice seeing her in such a submissive position."
    davide "Want to see something else, come here [pov]!"
    scene basement 2am 004a
    pov "Oh..."
    davide "I already widen her hole a little."
    pov "I see, but it's still to small. I hope you use much lube or it'll be very painful."
    ls "Hnng! Hnng!"
    davide "Relax girl!"
    if inc == True:
        davide "Your brother is making fun of it."
    else:
        davide "[pov] is making fun of it."
    pov "Haha."
    ls "Hmm..."
    davide "I use just a small amount because she should also feel how she get pierced."
    scene basement 2am 005a
    pov "Damn, that'll be really a hard ride."
    ls "Hnng?"
    davide "The tip is almost in. Your lubed hole is sucking me slowly in."
    pov "Don't break her, haha."
    davide "She needs to learn to get fucked good."
    scene basement 2am 006a
    davide "There we go!"
    ls "HNNG!"
    davide "All in!"
    if inc == True:
        pov "Damn! He's deep inside my little sister with his big dick."
    else:
        pov "Damn! He's deep inside [ls] with his big dick."
    scene basement 2am 007a
    ls "Hnng! Hnng!"
    davide "Oh yes! Your tight asshole is clinging on my dick."
    davide "Your tightness is a dream!"
    ls "Hnng! Hnng!"
    davide "Stop trying to press me out! I'll mark your asshole, no matter what!"
    pov "Oh they're even some tears."
    davide "They're needed to show that she's putting some effort in it."
    pov "Hmm, that's also a way to explain..."
    davide "She can bear it. She need to, if she wants to be a good girlfriend."
    scene basement 2am 008a
    davide "Much better!"
    ls "Hnn... hnn..."
    pov "She seems to be more relaxed."
    davide "Yes, she is. It's like a dream to fuck that small hole!"
    ls "Hnn... hnn..."
    davide "She's working hard to be my slut!"
    pov "{i}Damn it! Lucky bastard!{/i}"
    "Davide fuck her faster."
    scene basement 2am 009a
    ls "Hgg... hgg..."
    pov "Oh she's about to faint. Don't overdo it!"
    davide "Hell yeah. She did good work, I'm already at my limit."
    davide "No need to faint, slut! Just endure it a little longer."
    davide "I'm... HNNG! HNNG! Yes, I mark you!"
    ls "HGGG..."
    scene basement 2am 010a
    davide "Damn! She can't take it inside. It spraying out of her."
    ls "Hnnn..."
    pov "{i}And she even got humiliated at her first time.{/i}"
    davide "Come here, look at this mess."
    scene basement 2am 011a
    pov "Wow! That hole is really widen."
    davide "Yes, she took me deep."
    scene black
    "Davide untied [ls]."
    scene basement 2am 012a
    ls "Did I well? Are you satisfied with me, lover?"
    davide "Hm... so, so. It could be still better..."
    ls "But I really tried."
    pov "{i}Damn, even now he's talking her into the way he wants her to be.{/i}"
    pov "{i}And she's already fallen for his talking.{/i}"
    scene basement 2am 013a
    pov "{i}And the much cum he shot on her. It's still dripping.{/i}"
    pov "{i}She's fixed just at him.{/i}"
    if inc == True:
        pov "{i}She don't even care that she's staying naked in front of her brother with cum dripping out of her asshole.{/i}"
        ls "Brother?"
    else:
        pov "{i}She don't even care that she's staying naked in front of me with cum dripping out of her asshole.{/i}"
        ls "[pov]?"
    pov "Hm?"
    scene basement 2am 014a
    davide "What's your judgment of her performance?"
    ls "Did I ruin it?"
    pov "{i}I still can't believe it.{/i}"
    if inc == True:
        pov "No, I think you did good, lil sis."
    else:
        pov "No, I think you did good [ls]."
    davide "Hm, maybe [pov] is right. It was very good for your first time taking a black dick!"
    scene basement 2am 015a
    ls "Oh thank you! I did good!"
    davide "Yes I already said that slut!"
    pov "..."
    ls "I took it in the back for the first time and made my boyfriend happy."
    davide "So you want to be an ass-slut?"
    scene basement 2am 016a
    if inc == True:
        ls "You hear that, brother? I made Davide happy and was a good ass-slut!"
    else:
        ls "You hear that, [pov]? I made Davide happy and was a good ass-slut!"
    pov "{i}And there's the rest of here innocence going away...{/i}"
    davide "It's just the adrenaline, slut. You gained it through my sperm. Next time we'll see how you can do again."
    ls "I'll give my best, lover."
    davide "So you had a fine show [pov], but I think it's time that we leave."
    davide "Bruce and [mother] are still drunk, but I won't risk us getting caught."
    davide "It's still to soon to let them know."
    ls "Haha, mom will be so mad."
    davide "You go first, [ls] can go then a little later."
    pov "OK. No problem. Bye Davide, bye ass-slut, haha."
    ls "Haha..."
    scene black
    "You leave the basement and go back to your room."
    "A while later you hear [ls] going to her room too."
    $ base2likentr = False
    $ meet4am = False
    $ base2amalexisntrfirst = True
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    if hardntr == False:
        jump stats
    elif hardntr == True:
        jump statshard

label base2hide:
    pov "{i}I need to see this but they don't need to know.{/i}"
    "You hide silently at the armchair."
    scene basement 2am 002b
    pov "{i}What? She's seeing me! But she don't anything to make him notice.{/i}"
    pov "{i}So she's okay with me watching.{/i}"
    call screen base2amlike

screen base2amlike():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_approve_%s.png" xpos 1209 ypos 81 action (Hide ('base2amlike'), Jump('base2approve')) hovered tt.Action ("Like NTR") focus_mask True
        imagebutton auto "gui/icons/icon_disapprove_%s.png" xpos 1383 ypos 81 action (Hide ('base2amlike'), Jump('base2disapprove')) hovered tt.Action ("Hate NTR") focus_mask True


    frame:
        xalign .5
        text tt.value

label base2approve:
    $ base2likentr = True
    jump base2disapprove

label base2disapprove:
    pov "{i}But what's he doing? Deflowering her while she's restraint like a fucktoy?{/i}"
    if base2likentr == False:
        pov "{i}That damn fucker! She don't deserve it to get it that way.{/i}"
    davide "Your tight asshole will love my dick, slut!"
    ls "Hnn..."
    pov "{i}Oh he's deflowering her asshole.{/i}"
    if base2likentr == False:
        pov "{i}But it's still wrong. I wish I could stop it but I'm sure he'll beat me to death.{/i}"
        pov "{i}I can't stand against him!{/i}"
    davide "There we go, slut!"
    scene basement 2am 003b
    ls "HNNG!"
    scene basement 2am 004b
    davide "All in!"
    ls "HNNG!"
    if base2likentr == True:
        pov "{i}Damn, did he really go all in with one hit?{/i}"
        pov "{i}Spreading her tight asshole.{/i}"
    else:
        pov "{i}He's humiliating her. Raping her asshole and she's helpless.{/i}"
        pov "{i}And even in pain. What did he do with her that she's letting him do that to her?{/i}"
    "Davide is fucking her faster."
    scene basement 2am 005b
    davide "Perfect. Your tight slut-hole is clinging on my dick!"
    ls "Hnng... hnng..."
    davide "You make me proud. I hadn't such a tight hole since a long time."
    if base2likentr == False:
        pov "{i}She's crying! You need to stop asshole!{/i}"
    scene basement 2am 006b
    ls "Hnn... hnn..."
    davide "You relaxed yourself now? Good. So I can fuck you faster!"
    pov "{i}She's staring at me again! But I'm not sure what's with her eyes.{/i}"
    if base2likentr == True:
        pov "{i}Is she sad that I see her getting humiliated by her \"loving boyfriend\"?{/i}"
        pov "{i}Haha, but I'm enjoying her performance.{/i}"
    else:
        pov "{i}Do she want me to rescue her from her humiliation?{/i}"
        pov "{i}But I can't. Please be strong [ls].{/i}"
    scene basement 2am 007b
    ls "Hgg... hgg..."
    if base2likentr == True:
        pov "{i}Damn, he's plugging her so hard that she's about to faint.{/i}"
        pov "{i}This must be really a good fucking.{/i}"
    else:
        pov "{i}He's raping her so hard that she's about to faint!{/i}"
        pov "{i}Stop it! You'll break her!{/i}"
    davide "AH! I'm cumming, slut! I'll mark you as mine!"
    ls "HGGG!"
    scene basement 2am 008b
    ls "Hnn... hnn..."
    davide "Look at this mess. It's so much, it's spraying out of your tight hole!"
    if base2likentr == True:
        pov "{i}He really marked her!{/i}"
    else:
        pov "{i}She's so humiliated! Being used like a fucktoy.{/i}"
    davide "I can't wait to wide it even more next time."
    scene black
    "Davide untied [ls]."
    scene basement 2am 009b
    ls "Did I well? Are you satisfied with me, lover?"
    davide "Hm... so, so. It could be still better..."
    ls "But I really tried."
    pov "{i}Damn, even now he's talking her into the way he wants her to be.{/i}"
    pov "{i}And she's already fallen for his talking.{/i}"
    scene basement 2am 013a
    if base2likentr == True:
        pov "{i}And that tight ass pressing his cum out. What a hot view.{/i}"
    else:
        pov "{i}He stole her innocence! He must die!{/i}"
    davide "But if you give your best, you can be a good ass-slut in no time!"
    ls "Then... I'll try..."
    scene basement 2am 010b
    ls "Trust me lover, I'll be the best ass-slut!"
    if base2likentr == True:
        pov "{i}Did she liked it that much or does she just want to do everything for her \"boyfriend\"?{/i}"
    else:
        pov "{i}He already broke her. Brainwashed her with that \"slut-shit\"! She's not pure anymore.{/i}"
    davide "Oh with me training you, you'll be one in no time, haha."
    ls "Good, my lover...<giggle>"
    scene basement 2am 011b
    ls "I'll be the best girlfriend ever for you."
    davide "I would recommend the best slut ever!"
    ls "Then I'll be the best slut ever!"
    if base2likentr == True:
        "Fascinated by the work Davide did to her you leave them silently."
    else:
        "Shocked about what you saw you leave them silently."
    $ base2likentr = False
    $ meet4am = False
    $ base2amalexisntrfirst = True
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    if hardntr == False:
        jump stats
    elif hardntr == True:
        jump statshard


label base4amal:
    $ showbasealfirst = True
    scene basement 4am 001
    "You see [ls] waiting eagerly."
    ls "So what is it? Show me!"
    pov "We're going to the basement now."
    scene basement 4am 002
    if basealefirst == True:
        ls "But this isn't something special, we were already there."
        pov "Oh this time will be special, because we use another way to get in."
        ls "Another way?"
    else:
        ls "Are you kidding me? How should we enter?"
        pov "I'll show you."
    "You unlock the door with your key."
    scene basement 4am 003
    ls "Wow! You opened it."
    pov "Yes, the secret room."
    ls "So this means you're a gang-member now?"
    pov "Yes, I'm a special one now, haha."
    scene basement 4am 004
    ls "You're really a gang member now. Or did you just steal the key?"
    pov "No, I'm serious. I'm part of the gang now."
    pov "But if you don't believe me, we can stop this and you can get back to bed."
    scene basement 4am 005
    ls "No, I'll believe you, I don't want miss this chance."
    pov "Good idea. But we have to be silent."
    if inc == True:
        ls "And my big brother won't lie to me, would he?"
    else:
        ls "And you won't lie to me, would you?"
    pov "Never, haha."
    scene basement 4am 006
    ls "I'm so special, lalala..."
    pov "What are you doing? You've gone crazy?"
    ls "<giggle> I came through the door."
    pov "{i}She's enjoying this new secret.{/i}"
    scene basement 4am 007
    ls "It's so cool to be here with you and mom doesn't know."
    pov "Yes but it could get really bad if she knew."
    if inc == True:
        ls "My big brother is now a gang-member and shows me the secret hideout."
    else:
        ls "You're now a gang-member and show me the secret hideout."
    ls "I feel so special and much better then [bs]."
    pov "Why?"
    ls "She isn't allowed to go here. <giggle>"
    scene basement 4am 008
    ls "And look at that, a blue drink, so cool."
    pov "You won't start drinking yet?"
    ls "Haha, maybe?"
    pov "{i}She's so happy now.{/i}"
    scene basement 4am 009
    ls "So blue!"
    if basenicfirst == True:
        if inc == True:
            pov "{i}The same behavior as mom. Falling for the blue drink.{/i}"
        else:
            pov "{i}The same behavior as [mother]. Falling for the blue drink.{/i}"
    pov "Don't drink too much or you'll get drunk and we'll get caught."
    ls "Don't worry... so blue..."
    scene basement 4am 010
    "She turns around."
    pov "Take care of your drink."
    ls "<giggle> I was thinking..."
    pov "What?"
    ls "A changing room."
    pov "Oh and what's your idea now?"
    pov "{i}I have a good feeling.{/i}"
    scene basement 4am 011
    ls "I want to try something."
    pov "OK. But take care and don't ruin something."
    ls "Haha, I'm not stupid."
    pov "Fine."
    ls "I'll surprise you!"
    pov "{i}Or should I guide her while she's with me?{/i}"
    call screen base4amchoose

screen base4amchoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_corruption_%s.png" xpos 915 ypos 341 action (Hide ('base4amchoose'), Jump('base4amcor')) hovered tt.Action ("Choose for her [cr1]") focus_mask True
        imagebutton auto "gui/icons/icon_love_%s.png" xpos 1125 ypos 341 action (Hide ('base4amchoose'), Jump('base4amlove')) hovered tt.Action ("Let her choose [lv1]") focus_mask True


    frame:
        xalign .5
        text tt.value

label base4amcor:
    $ lilsiscorruption += 1
    pov "I'll choose something for you."
    scene basement 4am 012c
    ls "But why? I can do that alone."
    pov "I brought you here with me, even when I could get into trouble."
    pov "So I think it's only fair you do that for me."
    pov "And I let you be special, that's your words."
    ls "Hm... OK."
    pov "And put some makeup on for our special occasion."
    ls "Yes, I'll do it for you."
    scene basement 4am 013
    "You choose something for her."
    ls "This one, but..."
    pov "Just try it on, maybe I have something else for you."
    ls "Something else?"
    pov "Yes it's special too."
    pov "{i}Maybe it's time to test the sex-drug on her?{/i}"
    scene basement 4am 014c
    pov "Wow!"
    if inc == True:
        ls "I feel so uncomfortable in this, brother."
    else:
        ls "I feel so uncomfortable in this, [pov]."
    pov "But you look very sexy."
    ls "Hnn..."
    scene basement 4am 015c
    if inc == True:
        pov "I can't believe I have such a hot lil sister."
    else:
        pov "I can't believe that you're so hot, [ls]."
    ls "Why are you saying this?"
    pov "Because it's true. You should wear this outfit more often around me."
    ls "Hnn..."
    pov "Now turn around and let me see the back of it."
    ls "O... OK."
    scene basement 4am 016c
    pov "This is getting even better."
    ls "What do you mean?"
    pov "You look even hotter from behind."
    ls "Please stop that..."
    pov "But it's true."
    scene basement 4am 017c
    ls "I think we should stop this now. Your behavior is so weird."
    pov "Haha, relax [ls]."
    pov "Did you forget the other special thing I have for you?"
    ls "Then what is it?"
    pov "A very delicious candy."
    scene basement 4am 018cc
    ls "Did you say candy?"
    pov "Yes and I think you can have it now, because you did what I wished."
    ls "So you just played with me?"
    pov "Haha, you want the candy now?"
    ls "Yes please give it to me."
    pov "Fine. Open your mouth."
    scene basement 4am 019cc
    ls "But why didn't you just give me it?"
    pov "You want it or not?"
    ls "OK. Please give me the candy."
    pov "{i}I'm so excited. How will she react? And what can I do with her, after getting so horny.{/i}"
    scene basement 4am 020cc
    ls "Ohh... this tastes good."
    if inc == True:
        ls "Thank you so much for it, big brother."
    else:
        ls "Thank you so much for it, [pov]."
    pov "You're welcome."
    pov "{i}I'm sure you'll thank me later in an other way too.{/i}"
    ls "<giggle> You're so nice."
    scene basement 4am 020c1c
    ls "Something is wrong."
    pov "What is it?"
    ls "I'm feeling... so hot..."
    pov "{i}Oh it starts working. Good.{/i}"
    ls "And there's another weird feeling."
    pov "Can you describe it?"
    ls "It's like a tickle."
    pov "{i}So the drug is working already. Now I need a way to test it.{/i}"
    pov "I have an idea, I'll check up on you."
    ls "A check up?"
    pov "Yes, trust me, it'll make you feel better."
    ls "..."
    if inc == True:
        pov "I'm your big brother, I know what's good for you."
    else:
        pov "I'm your older friend, I know what's good for you."
    pov " Come with me."
    scene basement 4am 021cc
    ls "I don't get it why you stuck me in this thing."
    pov "You said you have a tickle. So it's to protect me so you can't kick me accidentally."
    ls "<giggle> So you need to stay aware."
    pov "{i}So is the drug making people dumb, or just more comfortable in certain situations?{/i}"
    pov "I'll check your other site now, but you have to stay silent, no matter what happens."
    pov "Getting caught will be even worse."
    ls "Ok, you can do it [pov]."
    pov "{i}You have no idea, haha.{/i}"
    scene basement 4am 022cc
    pov "{i}Laying there all helpless before me.{/i}"
    pov "{i}And now even drugged with a strong one.{/i}"
    pov "{i}I can't wait, I need to check.{/i}"
    "You remove her panties."
    scene basement 4am 023cc
    if inc == True:
        ls "Did something change, brother?"
        pov "Why you asking?"
        ls "I feel a little sxposed."
        pov "No, everything is alright, lil sis."
    else:
        ls "Did something change, [pov]?"
        pov "Why you asking?"
        ls "I feel a little exposed."
        pov "No, everything is alright, [ls]."
    pov "She's already wet. Let's see how her body reacts."
    scene basement 4am 024cc
    "You touch her clit."
    ls "Hnn..."
    ls "Why you're touching me there?"
    pov "I need to find out why you feel the tickle."
    pov "Now be a good girl and stay silent."
    ls "OK. Hnn..."
    pov "{i}Damn, that's almost too easy. She's acting like a doll.{/i}"
    scene basement 4am 025cc
    ls "Hah..."
    pov "Sshh..."
    ls "Hnng..."
    pov "{i}Her tight pussy. I can also feel her hymen.{/i}"
    pov "{i}Maybe it's time to break it. With the sex-drug she may feel very good.{/i}"
    scene basement 4am 026cc
    pov "{i}And so damn wet. This drug is very strong. I'll have much fun with her.{/i}"
    pov "{i}Let's try something else.{/i}"
    scene basement 4am 027cc
    ls "Hah, your finger is..."
    pov "Yes I need to check everywhere."
    if lsispronanal >= 4:
        ls "So deep in me."
        pov "{i}Her asshole is clinging on my finger.{/i}"
        pov "{i}So she really takes pleasure from the anal porn I showed her.{/i}"
        ls "Hnng..."
        pov "{i}She doesn't even try to push me out, more like sucking me in.{/i}"
        pov "{i}Maybe this is a better hole.{/i}"
    scene basement 4am 028cc
    pov "{i}That gap.{/i}"
    if lsispronanal >= 4:
        pov "{i}So she already masturbated to anal porn. Her hole is somewhat elastic.{/i}"
        pov "{i}I wonder what she shove in to have fun.{/i}"
    scene basement 4am 029cc
    "You also reveal her tits."
    ls "You're already done...?"
    pov "{i}Wow, did I hear regrets? Is she hoping for some more?{/i}"
    pov "No, I'm just thinking for a second."
    ls "Please make that tickle feeling go away."
    if inc == True:
        ls "Help me, big brother."
        pov "{i}I can't believe it. My little sister is asking me to do naughty things with her.{/i}"
    else:
        ls "Help me [pov]."
        pov "{i}I can't believe it. [ls] is asking me to do naughty things with her.{/i}"
    pov "{i}So, what to do to help her?{/i}"
    call screen base4amcorchoose

screen base4amcorchoose():
    default tt = Tooltip (" ")

    fixed:
        if alexisvirgin == True:
            imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 500 ypos 197 action (Hide ('base4amcorchoose'), Jump('base4amcorpussy')) hovered tt.Action ("Deflower her pussy") focus_mask True
        if alexisvirgin == False:
            imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 500 ypos 197 action (Hide ('base4amcorchoose'), Jump('base4amcorpussy')) hovered tt.Action ("Fuck her pussy") focus_mask True
        if lsispronanal >= 4:
            imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 260 ypos 456 action (Hide ('base4amcorchoose'), Jump('base4amcorass')) hovered tt.Action ("Deflower her asshole") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1547 ypos 315 action (Hide ('base4amcorchoose'), Jump('base4amcorbj')) hovered tt.Action ("Use her mouth") focus_mask True


    frame:
        xalign .5
        text tt.value

label base4amcorpussy:
    if alexisvirgin == True:
        pov "{i}I need to deflower her pussy now. I can't wait any longer!{/i}"
    else:
        pov "{i}I need to fuck her pussy now. I can't wait any longer!{/i}"
    if inc == True:
        pov "I'll help you in a special way now, lil sis."
    else:
        pov "I'll help you in a special way now, [ls]."
    pov "Just try to relax and trust me."
    ls "Yes, please help me."
    scene basement 4am 030ccp
    "You push your the tip of your dick slowly in her."
    ls "Hnn... you want to go inside me..."
    if inc == True:
        pov "Yes it's time, lil sis."
    else:
        pov "Yes it's time, [ls]."
    ls "Your penis is so hot."
    pov "{i}Wow, she's so horny and willing.{/i}"
    if alexisvirgin == True:
        pov "I'll deflower you now and then you'll feel much better."
        if inc == True:
            ls "Yes... deflower me... brother."
        else:
            ls "Yes... deflower me... [pov]."
    pov "{i}Damn.{/i}"
    "You push deeper slowly."
    with vpunch
    "BOOM!"
    pov "What the hell?"
    mom "Ouch!"
    if daddead == False:
        dad "Everything alright?"
    scene basement 4am 031ccp
    pov "{i}This can't be happening right now.{/i}"
    mom "Did you leave the light on in the basement?"
    if daddead == False:
        dad "No, I don't think so."
    mom "I'll check!"
    if daddead == False:
        dad "Wait a second, your too drunk you could fall, I'll be there soon."
    jump base4amcorpussygo










label base4amcorass:
    pov "{i}I need to fuck her asshole now. I can't wait any longer!{/i}"
    if inc == True:
        pov "I'll help you in a special way now, lil sis."
    else:
        pov "I'll help you in a special way now, [ls]."
    pov "Just try to relax and trust me."
    ls "Yes, please help me."
    scene basement 4am 030cca
    "You push the tip of your dick in her asshole."
    ls "Hnn... You want to go in my asshole."
    if inc == True:
        pov "Yes it's time, lil sis."
    else:
        pov "Yes it's time, [ls]."
    pov "You already know much about it."
    ls "Your penis is so hot."
    pov "{i}Wow, she's so horny and willing.{/i}"
    pov "I'll fuck your asshole now and then you'll feel much better."
    ls "My asshole... hah..."
    scene basement 4am 032cca
    "You go deeper slowly."
    ls "Hnng... it's so thick."
    pov "And your tight hole is clinging."
    pov "You waited for this, didn't you?"
    ls "I... yes..."
    pov "Just masturbating about it and playing with your fingers isn't enough."
    if inc == True:
        ls "Yes brother, hah... please do more."
    else:
        ls "Yes [pov], hah... please do more."
    scene basement 4am 033cca
    "You push your dick almost all in."
    ls "Hnng... hnng..."
    if inc == True:
        pov "You feel your brother's dick fucking your asshole?"
        ls "Yes, it's so hot. It's burning me up, brother."
    else:
        pov "You feel my dick fucking your asshole?"
        ls "Yes, it's so hot. It's burning me up, [pov]."
    pov "I'll start to move now and fuck you!"
    ls "O... OK. Hnng..."
    scene basement 4am 034cca
    "You fuck her in her asshole."
    ls "Hah... ahhh... hah"
    pov "You like to get fucked in your asshole?"
    ls "Yes... yes, more... please more."
    pov "Then I'll help you to feel even better."
    scene basement 4am 036cca
    "You play with her clit too."
    ls "Hah... hnn... it's so good."
    pov "I'm glad you like it."
    ls "More... please more..."
    pov "{i}She's at her limit, so it's time that I mark her hole for me.{/i}"
    pov "You'll cum soon, I want to put my sperm in your asshole too."
    if inc == True:
        ls "Yes brother, hah... put your sperm in me..."
    else:
        ls "Yes [pov], hah... put your sperm in me..."
    pov "{i}Damn, now I know why this drug is so special.{/i}"
    pov "HNG!"
    "You spray your sperm in her asshole!"
    scene basement 4am 037cca
    ls "I'm... hah... cumming..."
    if inc == True:
        ls "I'm cumming from your dick brother!"
    else:
        ls "I'm cumming from your dick [pov]!"
    pov "Good girl!"
    ls "Hnng... hnng..."
    pov "That was a very good fuck."
    "You pull your dick out."
    scene basement 4am 038cca
    pov "{i}Look at this mess. Her asshole gaping with my cum dripping out.{/i}"
    ls "Hnng... hnn..."
    pov "I came so much inside you [ls]."
    ls "Yes I can feel it in me, hah... so hot..."
    "You release her."
    scene basement 4am 040cca
    ls "Hah, hnng..."
    pov "What's wrong [ls]?"
    pov "Did you hurt yourself?"
    ls "My legs are so weak. I can't stand up."
    pov "{i}Damn, that ass-fucking costs her strength.{/i}"
    pov "I'll help you."
    scene basement 4am 041cca
    "You hold her."
    pov "You liked it that much that you're done now?"
    ls "It was so intense!"
    if inc == True:
        pov "So the first time having sex with your brother was a good thing?"
    else:
        pov "So the first time having sex with me was a good thing?"
    ls "Y... yes, I liked it."
    pov "But why then that face?"
    ls "I'm... so tired..."
    pov "Oh, I see."
    pov "I'll bring you back to your bed."
    scene black
    "You bring her to her bed and go back to sleep."
    $ meet4am = False
    jump skip

label base4amcorbj:
    pov "{i}I want to have fun with her mouth. I can't wait any longer!{/i}"
    if inc == True:
        pov "I'll help you in a special way now, lil sis."
    else:
        pov "I'll help you in a special way now, [ls]."
    pov "Just try to relax and trust me."
    ls "Yes, please help me."
    scene basement 4am 030ccm
    ls "You want to help me with your penis?"
    pov "Yes I'll stick it in your mouth and it'll help you."
    ls "I don't know."
    if inc == True:
        pov "Just trust me, lil sis."
        ls "OK, brother."
    else:
        pov "Just trust me, [ls]."
        ls "OK, [pov]."
    scene basement 4am 031ccm
    pov "Here, taste it first."
    ls "OK, hm..."
    pov "Yes use also your tongue on it."
    ls "<lick>"
    if inc == True:
        pov "Hng... you're doing very good, lil sis."
    else:
        pov "Hng... you're doing very good, [ls]."
    scene basement 4am 032ccm
    "You hold her head so you can push your dick deeper in."
    ls "Hmpf..."
    pov "Good, suck on it."
    ls "<suck> <lick>"
    pov "You're doing very good and I bet the tickle feeling is also gone."
    ls "Hnn... yesh..."
    scene basement 4am 033ccm
    pov "Just a little more."
    ls "Hmpf! <choke>"
    pov "It's almost a real deep-throat."
    if inc == True:
        pov "You please me good, lil sis."
    else:
        pov "You please me good, [ls]."
    ls "<choke> Hnng..."
    "You start to fuck her mouth."
    pov "This is the right thing."
    scene basement 4am 034ccmm
    ls "Hnng... hnng..."
    pov "Oh, I'm about to cum."
    if inc == True:
        pov "Swallow it all, lil sis."
    else:
        pov "Swallow it all, [ls]."
    ls "HNNG! <choke>"
    pov "HNG! Yes!"
    "You spurt your sperm down her throat."
    ls "<gulp> <gulp>"
    pov "Good, drink it all down."
    scene basement 4am 035ccmm
    ls "Bleh!"
    pov "It was a little much?"
    ls "Yes... I could barely swallow it."
    pov "{i}Oh, she isn't even upset or something. The drug must make all sexual actions better.{/i}"
    if inc == True:
        pov "You liked it, getting your brother's sperm?"
    else:
        pov "You liked it, getting my sperm?"
    ls "Yes... so thick..."
    scene basement 4am 036ccm
    pov "Everything alright, you look so weird."
    ls "My jaw hurts..."
    pov "Oh that'll get better. You just need more training."
    ls "More training?"
    pov "Yes it won't hurt anymore if I fuck your mouth more often."
    ls "You want to fuck my mouth more often?"
    pov "Yes it was very good."
    scene basement 4am 037ccm
    if inc == True:
        ls "Then you can do it, brother. When I help you feel that good."
    else:
        ls "Then you can do it, [pov]. When I help you feel that good."
    pov "So you could even become my personal cum-dumpster."
    ls "Cum-dumpster? <giggle>"
    pov "{i}Damn, that drug could make it worse.{/i}"
    pov "Yes but enough for now, we should go now. We'll have fun next time."
    ls "OK. Let's go."
    scene black
    "You go back to your rooms."
    $ meet4am = False
    jump skip


label base4amlove:
    $ lilsislove += 1
    pov "Then surprise me."
    scene basement 4am 013
    ls "Let's see."
    pov "{i}I wonder what she'll choose?{/i}"
    pov "{i}Maybe I'm lucky and it's something hot.{/i}"
    scene basement 4am 014l
    ls "Nice, isn't it?"
    pov "Oh yes, it's beautiful."
    ls "I loved it at first sight!"
    if inc == True:
        pov "It's looking really good on you, lil sis."
    else:
        pov "It's looking really good on you, [ls]."
    scene basement 4am 015l
    pov "{i}Damn, this thing is also transparent.{/i}"
    pov "{i}I can almost see her nipples. And that's damn sexy.{/i}"
    if inc == True:
        ls "You're done inspecting me, brother?"
    else:
        ls "You're done inspecting me, [pov]?"
    pov "Yes, almost."
    scene basement 4am 016l
    ls "And that fabric is so incredible soft. I'm in love with it."
    pov "Hmm..."
    ls "Is something wrong?"
    call screen base4amlovechoose

screen base4amlovechoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_love_%s.png" xpos 668 ypos 233 action (Hide ('base4amlovechoose'), Jump('base4amlovetell')) hovered tt.Action ("Tell her [lv1]") focus_mask True
        imagebutton auto "gui/icons/icon_abort_%s.png" xpos 1301 ypos 233 action (Hide ('base4amlovechoose'), Jump('base4amlovemute')) hovered tt.Action ("Don't tell her") focus_mask True


    frame:
        xalign .5
        text tt.value

label base4amlovetell:
    pov "[ls]?"
    ls "What is it?"
    pov "That top is somewhat transparent. I almost can see your nipples."
    scene basement 4am 017la
    ls "I know."
    pov "What? You know?"
    ls "Yes, but can you understand how much I like this thing. So soft."
    pov "So you don't care that I can see you?"
    ls "You can't see much, the pattern hides most. But I love this thing."
    pov "Yes, you mentioned that."
    ls "Are you making fun of me?"
    pov "No."
    jump base4amlovemute

label base4amlovemute:
    pov "..."
    ls "You want to see my back now?"
    pov "Sure."
    scene basement 4am 017l
    pov "Oh that's beautiful."
    ls "I like it too."
    scene basement 4am 018l
    pov "{i}Damn, those panties are also transparent. And so hot.{/i}"
    pov "Those panties look really good on you, [ls]."
    ls "Thank you [pov]."
    scene basement 4am 018la
    ls "So I made a good choice?"
    pov "Not a good, a very good choice."
    ls "<giggle> It's good that you like it."
    pov "{i}You have no idea.{/i}"
    scene basement 4am 019l
    ls "I have to thank you for bringing me here so I can find this treasure."
    pov "Oh so you're in love now with these outfits?"
    ls "Yes and I plan to keep it. Sleeping in this thing would be the best thing ever."
    pov "But you can't!"
    ls "Why not?"
    pov "It'll get noticed and then someone's gonna find out."
    scene basement 4am 020l
    if inc == True:
        ls "But wouldn't it be a nice present for the best sister ever?"
        pov "I don't think that's a good idea, lil sis."
    else:
        ls "But wouldn't it be a nice present for the best childhood friend ever?"
        pov "I don't think that's a good idea, [ls]."
    ls "So it's decided. Thank you for the outfit!"
    pov "No! I said you have to leave it here. You just can't keep it."
    ls "And when I just go now to my room?"
    pov "Then would I get in big trouble."
    scene basement 4am 021l
    ls "So you're scared now?"
    pov "What?"
    if inc == True:
        ls "Because your fate is in your little sisters hands now!"
    else:
        ls "Because your fate is in my hands now!"
    pov "You're kidding me..."
    ls "You're my victim now! Let's see what I'm gonna do with you."
    pov "Hahaha..."
    scene basement 4am 022l
    "She jumps on you."
    if inc == True:
        ls "So you have to be a nice brother now or you'll get into trouble."
    else:
        ls "So you have to be a nice friend now or you'll get into trouble."
    pov "I give up. Show mercy, haha."
    ls "Good, you accepted it."
    scene basement 4am 023l
    ls "<kiss>"
    pov "Ohh..."
    ls "<kiss> <giggle>"
    scene basement 4am 024l
    ls "<kiss> <kiss>"
    pov "{i}Oh she climbed on me and is french kissing me. So this got her excited.{/i}"
    ls "<kiss> Hnn..."
    "You play with her tongue."
    scene basement 4am 025l
    ls "<giggle>"
    ls "I would never hurt my weak dummy."
    pov "Oh, so I'm weak now, haha."
    ls "Yes, giving up so fast."
    pov "Maybe I tricked you."
    scene basement 4am 026l
    pov "Counterattack!!"
    ls "Huh?"
    pov "<kiss>"
    ls "Hah..."
    "You kiss over her chest."
    ls "Hnn... hah... you dummy..."
    pov "{i}She's in the mood for more.{/i}"
    scene basement 4am 027l
    pov "<kiss>"
    "You kiss her nipple through the transparent top."
    ls "Hah... Hnn..."
    pov "{i}Her nipples are hard.{/i}"
    pov "<kiss> <lick>"
    ls "Hnng... hah..."
    scene basement 4am 028l
    ls "Hah... hah..."
    pov "So I got your plan now."
    ls "My, plan? Hnn..."
    "You pinch her nipple gently."
    ls "Aahh..."
    pov "Calling me weak so I have to show you that I'm not."
    ls "I... hah..."
    if inc == True:
        pov "Your nipples are hard, lil sis."
    else:
        pov "Your nipples are hard, [ls]."
    pov "So you liked my counterattack."
    ls "Your... hah..."
    pov "But don't worry, we're not done now."
    pov "And I'm sure you want me to go on."
    scene basement 4am 029l
    pov "First let me explore your body more."
    ls "Hah... your hand..."
    "You go lower."
    ls "Your hand is going... hah..."
    pov "Should I stop? Maybe my thoughts have gotten away."
    if inc == True:
        ls "No brother. Please attack me more, hah..."
        pov "As you wish, lil sis."
    else:
        ls "No [pov]. Please attack me more, hah..."
        pov "As you wish, [ls]."
    scene basement 4am 030l
    "You reach her pussy."
    pov "You're so wet."
    ls "I...know... hah..."
    pov "You sure that you want me to do more?"
    ls "Yes... please..."
    "You start to rub her clit through her panties."
    ls "Hnn... hah..."
    pov "That outfit gave me the right impression and that's the reason you wear it, isn't it?"
    ls "What... hah... do you mean?"
    pov "You wanted to be sexy for me."
    ls "Hnn... hah..."
    pov "Please tell me, I want to know if I'm right."
    ls "Yes! I wanted you to see me as a sexy girl."
    pov "I'm very happy now. You want even more?"
    ls "Yes, please more. I'm so close!"
    pov "Then enjoy yourself."
    scene basement 4am 031l
    ls "AAAHHH... HAAH..."
    if inc == True:
        ls "Brother, hah... hah..."
    else:
        ls "[pov], hah... hah..."
    pov "{i}So she's having an orgasm from me.{/i}"
    ls "Hnn... hnn..."
    scene basement 4am 032l
    ls "Hah... hah..."
    pov "So you're sure it was the right decision?"
    ls "Stop talking, just hold me."
    pov "OK. then I'll hol..."
    if inc == True:
        ls "I love you, brother!"
    else:
        ls "I love you, [pov]!"
    pov "Oh, I understa..."
    if inc == True:
        ls "But I love you, brother!"
        pov "Oh. I love you too, lil sis!"
    else:
        ls "But I love you, [pov]!"
        pov "Oh. I love you too, [ls]!"
    scene basement 4am 033l
    pov "That was a little intense. Are you alright?"
    ls "Yes... it was so good."
    pov "Yes and it was something new I could do for you."
    ls "So you understand my hint now."
    pov "Yes you did this because you love me."
    if inc == True:
        ls "Yes I love you so much, brother!"
    else:
        ls "Yes I love you so much, [pov]!"
    scene basement 4am 034l
    "She pushes you till you fall down."
    pov "What?"
    ls "It's your turn."
    pov "My turn?"
    ls "Now I'll make you feel good."
    pov "Oh... Ohh!"
    ls "<giggle> Let me see your thing."
    scene basement 4am 035l
    if inc == True:
        ls "Oh, your penis is so big, brother."
    else:
        ls "Oh, your penis is so big, [pov]."
    pov "Then take your pace, I don't want you to get hurt."
    ls "So... big..."
    pov "[ls]?"
    scene basement 4am 036l
    ls "Oh, I was just thinking of something. <giggle>"
    pov "What do you want to do with my penis?"
    ls "Yes! <giggle>"
    pov "Right now?"
    ls "Maybe...?"
    pov "You'll surprise me."
    ls "Yes, you'll like it."
    scene basement 4am 037l
    if inc == True:
        ls "You like my massage, big brother?"
    else:
        ls "You like my massage, [pov]?"
    pov "Yes, you're hands are very soft."
    ls "Then enjoy it as much as you can. I want to return the good feeling you gave me."
    pov "Oh I will, don't worry."
    ls "<giggle>"
    pov "{i}Damn, this is more then I could have dreamed of, I'll cum in no time.{/i}"
    scene basement 4am 038l
    ls "<kiss>"
    pov "Damn!"
    ls "<giggle> It's twitching so hard, maybe another kiss to calm down."
    ls "<kiss>"
    pov "That's too much!"
    scene basement 4am 039l
    pov "HNNG!"
    ls "Huh?"
    pov "That... was... so good..."
    ls "I see, you came."
    scene basement 4am 040l
    ls "I'm happy now that we both had a good time."
    pov "Me too."
    ls "So can I keep my outfit now? <giggle>"
    pov "I'm afraid not. It's just to risky. But I can buy you one."
    ls "Great, then we could have more good times together."
    pov "Haha, oh yes."
    ls "It's late, should we get back?"
    if inc == True:
        pov "Yes. and lil sis?"
        ls "Hm...?"
        pov "I love you!"
        ls "Aww... I love you too, big brother."
    else:
        pov "Yes, and [ls]?"
        ls "Hm...?"
        pov "I love you!"
        ls "Aww... I love you too, [pov]."
    scene black
    "You leave the basement together."
    $ meet4am = False
    jump skip


label casbasement:
    hide screen locations
    scene kitchen 9am 020
    if inc == True:
        bs "Hi, lovely brother!"
    else:
        bs "Hi, lovely [pov]!"
    pov "{i}Huh? What's up with her? Why that sweet-talk?{/i}"
    pov "What's up?"
    bs "I heard you're a gang member now."
    pov "Yes."
    if bigsiscorruption >= bigsislove:
        scene kitchen 9am 009rc
    else:
        scene kitchen 9am 006rl
    bs "So I wonder if you can let me join too?"
    bs "You know that I've wanted this for so long."
    pov "{i}Oh, so that was the reason?{/i}"
    pov "Hmm..."
    if inc == True:
        bs "Please, you'd be the best brother."
    else:
        bs "Please, you'd be the best [pov]."
    pov "{i}Is it the time to let her join too or should I let her wait some time longer?{/i}"
    call screen casbasementallow

screen casbasementallow():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_approve_%s.png" xpos 1604 ypos 206 action (Hide ('casbasementallow'), Jump('casbasementallowyes')) hovered tt.Action ("Let her join") focus_mask True
        imagebutton auto "gui/icons/icon_disapprove_%s.png" xpos 1604 ypos 405 action (Hide ('casbasementallow'), Jump('casbasementallowno')) hovered tt.Action ("Not now") focus_mask True


    frame:
        xalign .5
        text tt.value

label casbasementallowno:
    pov "No, it's to soon."
    bs "But why?"
    pov "You'll get your chance another time."
    bs "Hnn..."
    scene black
    $ dtime += 1
    jump kitchen

label casbasementallowyes:
    $ casbasecumface = False
    $ casbasecummouth = False
    $ casbasecumonass = False
    $ casbasecuminass = False
    pov "OK."
    bs "Really?"
    pov "Yes."
    scene kitchen 9am 021
    bs "Thank you so much."
    pov "But we'll go right now so I can show you everything."
    pov "And it'll be our secret for some time, until I decide to reveal it to the others."
    bs "So we go now because they're all out of the house."
    pov "Yes, let's go."
    if bigsiscorruption >= bigsislove:
        scene kitchen 9am 009rc
    else:
        scene kitchen 9am 006rl
    bs "But I'm still in my underwear."
    pov "There are clothes down there, you can wear something from there."
    bs "Oh, really?"
    pov "Yes, let's go. Now or never."
    scene kitchen 9am 021
    bs "OK."
    scene black
    "You go together into the basement."
    scene basement 9am 001
    bs "Wow, so it's real now. I'm in the basement!"
    bs "But it's a little weird here with that \"punishment\" corner."
    pov "I'll tell you later why it's here. I'm not sure if you'll like it."
    bs "Oh..."
    bs "And where are the clothes you mentioned?"
    pov "Back there."
    scene basement 9am 002
    pov "You can change in that little room. I'm sure you'll like it, there are many outfits inside."
    bs "So I can choose something?"
    call screen casbaseoutfitchoose

screen casbaseoutfitchoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_love_%s.png" xpos 467 ypos 123 action (Hide ('casbaseoutfitchoose'), Jump('casbasementlove')) hovered tt.Action ("Yes, choose one you like") focus_mask True
        imagebutton auto "gui/icons/icon_corruption_%s.png" xpos 1175 ypos 123 action (Hide ('casbaseoutfitchoose'), Jump('casbasementcor')) hovered tt.Action ("No, I'll choose one") focus_mask True


    frame:
        xalign .5
        text tt.value

label casbasementcor:
    $ bigsiscorruption += 1
    scene basement 9am 003c
    bs "What? But I thought..."
    pov "You wanted me to get you here, so you can do this for me now."
    bs "Hnn..."
    pov "And I'm sure you'll like it too. There are really good things in there."
    bs "O... OK."
    scene black
    "You choose something for her and she goes to change."
    scene basement 9am 020c
    bs "You can't be serious."
    pov "Why? You're looking really sexy in that outfit!"
    bs "It's like I'm almost naked."
    scene basement 9am 021c
    pov "You aren't. And your club outfit it's almost the same, so stop complaining."
    bs "But..."
    pov "You wanted me to get you here and I choose a sexy outfit for you."
    pov "So there is no need to be sad."
    bs "Hnn..."
    scene basement 9am 022c
    pov "And you can't deny that you'd love the attention you'd get in this outfit."
    pov "Seeing your hot long legs in that shoes."
    bs "You want me to wear this thing when others around?"
    scene basement 9am 024c
    pov "Why not?"
    bs "Hnng..."
    if inc == True:
        pov "Why not show everyone how hot my big sis is?"
    else:
        pov "Why not show everyone how hot you are?"
    pov "And also it's a good proof how obedient my girl is."
    scene basement 9am 023c
    bs "But I'm not your girl!"
    pov "No you aren't. Not now, but soon!"
    if inc == True:
        bs "I'm still your sister!"
    pov "You know that's just a matter of time until you give in and become my girl."
    pov "You want to be part of the gang to become famous and be someone."
    scene basement 9am 025c
    pov "And I'm your chance for that and you know that very well."
    pov "So you can keep denying or just admit that I'm right."
    pov "I can handle you much better then your looser boyfriend."
    bs "Hnng..."
    scene basement 9am 026c
    pov "You see the drink standing there? That will be one of your duties here, serving drinks."
    bs "Serving?"
    pov "Yes that's the role of the women down here. Wearing sexy outfits and serve."
    pov "{i}And serve in another way also, but she'll notice this very soon.{/i}"
    pov "Now move your sexy ass there and take a better look at your work."
    scene basement 9am 027c
    if inc == True:
        bs "So, mom has to do this also when she's here?"
    else:
        bs "So, my mom has to do this also when she's here?"
    pov "Yes and she's doing it very well, so you have to train it to be as good as her."
    scene basement 9am 028c
    pov "But I have to prepare some things before she can know that you're here too."
    pov "So it's your duty to train well so she will not complain to much."
    bs "I... understand."
    pov "{i}Her ass is almost naked. That outfit was a good choice.{/i}"
    scene basement 9am 029c
    pov "{i}And her long legs in that sexy heels.{/i}"
    pov "{i}I think she could where these more often.{/i}"
    scene basement 9am 030c
    bs "So I have to serve you the drinks or the other men later too?"
    pov "Oh good, now you show some interest."
    pov "We'll see when it's time, but mostly you're my girl, so I'm mainly the one you'll serve."
    bs "Stop..."
    pov "{i}Ha, she still hasn't realized what is coming.{/i}"
    scene basement 9am 031c
    pov "{i}That little pad over her pussy. I can't wait to remove it and put my dick inside.{/i}"
    pov "{i}This is making me so horny.{/i}"
    bs "Stop looking..."
    scene basement 9am 032c
    bs "Stop looking at me like that."
    pov "But you're my prize. A very good prize that is soon a part of our gang."
    pov "See it as a part of your entrance exam."
    bs "Hnn..."
    pov "Now let me show you the main thing about the basement."
    scene basement 9am 034c
    bs "What are these pills? Drugs?"
    pov "Yes, but better. These are sex-drugs!"
    scene basement 9am 035c
    bs "Sex-drugs?"
    pov "As I said. They're for women only. Giving them a strong sex drive."
    pov "They're very popular and we sell them here."
    scene basement 9am 036c
    bs "I won't take them. Just forget about it."
    pov "Haha, you really think I need them to have fun with you?"
    bs "What does that mean?"
    pov "I'll make you my girl the normal way, I don't need to \"cheat\"."
    scene basement 9am 037c
    bs "That's a good decision. I won't be your doll."
    pov "{i}Haha, is she realizing what she just said? Allowing me to make her my girl.{/i}"
    pov "{i}But she'll soon beg for the drugs when she sees them in \"action\".{/i}"
    bs "So can we start now? I have other things to do."
    pov "{i}Oh, her old personality is back. But well, I'll teach her the lesson she needs.{/i}"
    "You walk over to the couch."
    scene basement 9am 038c
    pov "Now it's time to serve me a drink."
    pov "{i}I can't stop staring at her.{/i}"
    if inc == True:
        pov "{i}I wonder how mom will react when she see her wearing this.{/i}"
    else:
        pov "{i}I wonder how [mother] will react when she see her wearing this.{/i}"
    bs "So what do you want to drink?"
    pov "Drink?"
    pov "Oh, sure. I think a wine is fine to celebrate your exam."
    scene basement 9am 039c
    pov "{i}Maybe I should skip the serving, stand up and just fuck her from behind?{/i}"
    pov "{i}What a strong tease she is in that \"dress\".{/i}"
    scene basement 9am 040c
    bs "There's only red wine. Do you want this?"
    pov "Yes, like other things!"
    bs "Other things?"
    pov "Hm... Bring the red wine and you need a glass too."
    scene basement 9am 041c
    bs "See? I can do this easy."
    pov "Yes and it's also good looking."
    bs "Hnng..."
    pov "{i}So what should I do with her as her entrance exam?{/i}"
    call screen casbasementcorchoose

screen casbasementcorchoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1143 ypos 134 action (Hide ('casbasementcorchoose'), Jump('casbasementcorbj')) hovered tt.Action ("Use her mouth") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1143 ypos 584 action (Hide ('casbasementcorchoose'), Jump('casbasementass')) hovered tt.Action ("Use her ass") focus_mask True


    frame:
        xalign .5
        text tt.value

label casbasementcorbj:
    pov "{i}Her blow-jobs are so good, so she can serve me good with them.{/i}"
    "You unpack your dick."
    scene basement 9am 042cb
    bs "What are you doing?"
    pov "Preparing the final step of your exam."
    bs "But..."
    scene basement 9am 043cb
    pov "Come closer, put the try down and serve me more."
    bs "Hnng..."
    pov "Don't play surprised. You knew about it the moment I agreed to let you down here."
    pov "And I know that you're eager to show me that your mouth is the best reason to choose you as my girl."
    scene basement 9am 044cb
    bs "Hnn..."
    pov "Oh, you're offended that I already know it, haha."
    if inc == True:
        pov "I know you much better than you think, big sis."
    else:
        pov "I know you much better than you think, [bs]."
    scene basement 9am 045cb
    bs "Hnn..."
    pov "Stop looking at me like that. It's time to start your duty."
    pov "Pass your final step to become a part of the basement."
    pov "And you could also be happy that we do this while we're alone and the others are not here."
    pov "{i}Haha, but that could also change very soon.{/i}"
    scene basement 9am 046cb
    pov "How about you show me more excitement?"
    pov "You could tell me what you want to do as your final step."
    pov "Hnn..."
    pov "Prove to me that I made a good decision taking you here."
    bs "I..."
    if inc == True:
        bs "I want to suck your dick as my final step, brother."
    else:
        bs "I want to suck your dick as my final step, [pov]."
    pov "Good girl. Now you can start."
    scene basement 9am 047cb
    pov "Yes, take a good look at your favorite dick."
    bs "Hmm..."
    pov "{i}I can't wait to feel her tongue again.{/i}"
    scene basement 9am 048cb
    bs "<suck> <lick>"
    pov "Yes, that's good."
    if inc == True:
        pov "{i}Letting my big sister prove that she can give the best blow-jobs.{/i}"
    else:
        pov "{i}Letting her prove that she can give the best blow-jobs.{/i}"
    scene basement 9am 049cb
    bs "Hah... <lick>"
    pov "{i}Oh, she opened wide to give her tongue more space.{/i}"
    if inc == True:
        pov "Your tongue are the best, big sis."
    else:
        pov "Your tongue are the best, [bs]."
    if casbjdt >= 2:
        jump casbasementdp
    scene basement 9am 050cb
    pov "Yes, lick it like a lollipop."
    bs "Hmm... <lick> <lick>"
    pov "You handle my dick even better this time."
    pov "I bet you don't put in so much effort when you did this with your boyfriend."
    bs "Hnng..."
    pov "Which will soon be your ex."
    scene basement 9am 051cb
    bs "<suck>"
    pov "Haha, nice trick to avoid an answer. I appreciate that."
    bs "Hmm..."
    scene basement 9am 052cb
    pov "Oh you stopped."
    bs "You know why."
    pov "Wow. Another reason why you have to be my girl."
    pov "You know exactly that I'm at my limit and need to cum now."
    bs "Yes, but where do you want me to take it."
    if inc == True:
        pov "You accept your role as a good girl very well, big sis."
    else:
        pov "You accept your role as a good girl very well, [bs]."
    call screen casbasementcorcum

screen casbasementcorcum():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1275 ypos 174 action (Hide ('casbasementcorcum'), Jump('casbasementcorcumf')) hovered tt.Action ("Cum on her face") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1275 ypos 314 action (Hide ('casbasementcorcum'), Jump('casbasementcorcumm')) hovered tt.Action ("Cum in her mouth") focus_mask True


    frame:
        xalign .5
        text tt.value

label casbasementcorcumf:
    $ casbasecumface = True
    pov "I want to spray it on your face."
    if inc == True:
        bs "OK, brother."
    else:
        bs "OK, [pov]."
    "She rubs your dick furiously."
    pov "Hah, so good."
    scene basement 9am 053cbo
    pov "Hnng..."
    bs "Hmm..."
    "You cum on her face."
    scene basement 9am 054cbo
    bs "Hnn... are you satisfied now?"
    pov "Yes, my girl. You served me well."
    bs "Hnng..."
    pov "{i}Ha, she still doesn't like it when I call her that.{/i}"
    pov "Don't wipe it off. It's my mark on you!"
    bs "Hmm..."
    jump casbasementcorend

label casbasementcorcumm:
    $ casbasecummouth = True
    pov "I want you to taste my sperm."
    if inc == True:
        bs "OK, brother."
    else:
        bs "OK, [pov]."
    "She rubs your dick furiously."
    pov "Hah, so good."
    scene basement 9am 053cbi
    pov "Hnng..."
    bs "Hmm..."
    "You cum in her mouth."
    scene basement 9am 054cbi
    bs "Aah..."
    pov "Good. You know what I want."
    pov "{i}Wow! Is she smiling?{/i}"
    if inc == True:
        pov "Now be a good girl and swallow your brothers present."
    else:
        pov "Now be a good girl and swallow my present."
    scene basement 9am 055cbi
    bs "<gulp>"
    pov "{i}I wonder why she likes it that much to swallow my sperm?{/i}"
    scene basement 9am 056cbi
    bs "Hnn... are you satisfied now?"
    pov "Yes, my girl. You served me well."
    bs "Hnng..."
    pov "{i}Ha, she still doesn't like it when I call her that.{/i}"
    jump casbasementcorend

label casbasementdp:
    $ casbasecummouth = True
    scene basement 9am 051cbdt
    bs "Hnng... <suck>"
    pov "Oh yes, you know exactly what I like."
    pov "{i}She's deep-throating me on her own. Training her was a good idea.{/i}"
    scene basement 9am 052cbdt
    pov "Holy shit!"
    bs "<suck> <choke>"
    pov "{i}She took me all in! And all on her own.{/i}"
    pov "{i}Surprising me like that. I won't last long.{/i}"
    bs "<suck> <choke>"
    pov "You do such a good job."
    scene basement 9am 053cbdt
    if inc == True:
        pov "I'm about to cum, big sis!"
    else:
        pov "I'm about to cum, [bs]!"
    pov "Taking me all in is such a good feeling."
    bs "<suck> <choke>"
    pov "Just let me spray it all down your throat and don't choke on it."
    bs "Hmm..."
    pov "Hold it just a moment longer!"
    pov "Hnng..."
    "You spray your sperm down her throat."
    bs "<gulp> <gulp>"
    scene basement 9am 056cbi
    bs "Hah... hah..."
    pov "That was almost perfect."
    bs "Hnn... are you satisfied now?"
    pov "Yes, my girl. You served me well."
    bs "Hnng..."
    pov "{i}Ha, she still doesn't like it when I call her that.{/i}"
    $ casbjdt += 1
    jump casbasementcorend


label casbasementass:
    pov "{i}Her ass needs a good pounding. I'm sure she'll claim her pussy is too sore now.{/i}"
    pov "Just put the tray on the table."
    bs "Yes..."
    scene basement 9am 042cf
    pov "Why you're looking at me like that? You're expecting something?"
    pov "{i}Does she have a clue what I'm up to?{/i}"
    bs "And now?"
    scene basement 9am 043cf
    bs "Huh?"
    pov "You know exactly what's happening now, don't you?"
    bs "Hnn..."
    pov "Go over there!"
    scene basement 9am 044cf
    bs "You can't fuck my pussy!"
    pov "Oh, don't worry. I won't."
    pov "{i}She only forbid me her pussy. Does she give me her other option on purpose?{/i}"
    scene basement 9am 045cf
    bs "What are you doing? I said you can't!"
    pov "Oh, I won't fuck your pussy. Your tight asshole is my target!"
    bs "You want to fuck my ass?"
    pov "Yes, as the final step of your entrance exam."
    scene basement 9am 046cf
    bs "But you can't..."
    pov "Oh yes, I can and I will. You'll let me use you to finish this here."
    bs "But..."
    pov "Also you can't wait for me to stick my dick inside you, can you?"
    bs "What are you talking about?"
    pov "I just said get over there and you bend over on your own!"
    bs "..."
    scene basement 9am 047cfa
    pov "And I'll give you a good pounding, so you can enjoy it too."
    bs "Hnn..."
    pov "So how about you ask me for finishing your exam with something we can both enjoy?"
    bs "Hnng..."
    pov "Prove to me that I took the right girl down here."
    if inc == True:
        bs "Please fuck my ass, brother."
    else:
        bs "Please fuck my ass, [pov]."
    pov "As you wish, my girl."
    scene basement 9am 048cfa
    bs "Hnn..."
    "You press your tip on her asshole."
    pov "Your asshole needs to get use to my big dick."
    bs "Hnn..."
    pov "And you need to remember your exam well."
    bs "Hnn..."
    scene basement 9am 049cfa
    bs "Aaaahhh...!"
    "You ram your dick all in!"
    pov "Hnn... so tight!"
    bs "Hnng..."
    if inc == True:
        pov "Just relax your muscles, big sis."
    else:
        pov "Just relax your muscles, [bs]."
    scene basement 9am 050cfa
    "You start to fuck her."
    bs "Hah... hah..."
    pov "I see you like your exam?"
    bs "Hah... hnng..."
    pov "Keep your ass tight to give me a good orgasm."
    scene basement 9am 051cfa
    "You release her tits."
    pov "Let them hang free and feel our fucking rhythm."
    bs "Hah... your... big dick..."
    pov "So you love it how my dick is widening your tight hole?"
    bs "Hah... hng..."
    scene basement 9am 053cfa
    "You pound her harder."
    pov "I'll cum soon, your tight hole is surprising me too much."
    bs "Hah... hah..."
    pov "So we need to fuck many times more so we can get used to it."
    bs "Hnng..."
    pov "So where do you want me to put my sperm? Deep inside you or on your ass?"
    bs "Hah... hah... hnng..."
    pov " You can't talk while I'm pounding you that hard? OK, I'll decide then."
    call screen casbasementcorasscum

screen casbasementcorasscum():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 470 ypos 501 action (Hide ('casbasementcorasscum'), Jump('casbasementcorassin')) hovered tt.Action ("Cum inside her ass") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 470 ypos 683 action (Hide ('casbasementcorasscum'), Jump('casbasementcorassout')) hovered tt.Action ("Cum on her ass") focus_mask True


    frame:
        xalign .5
        text tt.value

label casbasementcorassin:
    $ casbasecuminass = True
    pov "I'll cum inside your ass, my girl."
    pov "Hnng..."
    scene basement 9am 052cfa
    bs "Ohhh... Hnn..."
    if inc == True:
        pov "You feel my hot sperm spraying inside you, big sis?"
    else:
        pov "You feel my hot sperm spraying inside you, [bs]?"
    bs "Hnng... yes..."
    pov "Get used to it, I'll use it as my cum-dumpster."
    bs "Hah... hah..."
    scene basement 9am 053cfai
    pov "Oh yes, I released very much inside you!"
    bs "Hnng!"
    pov "Enjoy it as long as you can, haha."
    bs "Hnn... are you satisfied now?"
    pov "Yes, my girl. You served me good."
    bs "Hnng..."
    pov "{i}Ha, she still doesn't like it when I call her that.{/i}"
    jump casbasementcorend


label casbasementcorassout:
    $ casbasecumonass = True
    pov "I'll cum on your ass, my girl."
    pov "Hnng..."
    scene basement 9am 053cfao
    bs "Ohhh... Hnn..."
    if inc == True:
        pov "You feel my hot sperm spraying on your ass, big sis?"
    else:
        pov "You feel my hot sperm spraying on your ass, [bs]?"
    bs "Hnng... yes..."
    pov "This will mark you finally as mine."
    scene basement 9am 054cfao
    pov "Wonderful!"
    bs "Hnng..."
    bs "Are you satisfied now?"
    pov "Yes, my girl. You served me good."
    bs "Hnng..."
    pov "{i}Ha, she still doesn't like it when I call her that.{/i}"
    jump casbasementcorend

label casbasementcorend:
    scene black
    pov "Come, sit with me."
    if casbasecumface == True:
        scene basement 9am 060cf
    else:
        scene basement 9am 060
    pov "You did good, so we'll now drink together that you passed your exam."
    pov "Aren't you happy?"
    bs "Y... yes... I am."
    pov "You even got a physical mark for your success."
    if casbasecumface == True:
        scene basement 9am 061cf
    else:
        scene basement 9am 061
    if casbasecumface == True:
        pov "You did so good and my sperm on your face is the proof."
    elif casbasecummouth == True:
        pov "You did so good and my sperm in your stomach is the proof."
    elif casbasecumonass == True:
        pov "You did so good and my sperm on your ass is the proof."
    elif casbasecuminass == True:
        pov "You did so good and my sperm in your ass is the proof."
    bs "Hnng..."
    pov "Now show me that you admit it and drink your wine."
    bs "..."
    if casbasecumface == True:
        scene basement 9am 062cf
    else:
        scene basement 9am 062
    bs "<gulp> <gulp>"
    pov "{i}A big step to making her mine.{/i}"
    if casbasecumface == True:
        scene basement 9am 063cf
    else:
        scene basement 9am 063
    pov "Good girl. So how do you feel now to be part of the gang you wanted to join for so long?"
    bs "F... fine."
    pov "Then you can look forward to much more fun and \"serving\" here."
    bs "Hnng..."
    scene black
    "You leave the basement together."
    $ dtime += 1
    $ basecasfirst = True
    jump kitchen

label casbasementlove:
    $ bigsislove += 1
    scene basement 9am 003l
    bs "Cool!"
    bs "I'm excited what I can find there."
    scene black
    "She choose something and changed."
    scene basement 9am 020l
    bs "See what I found!"
    pov "Wow..."
    bs "Ha, so you like it too?"
    pov "Oh yes!"
    scene basement 9am 021l
    bs "Me too. I never thought I would find such a cool outfit down here."
    pov "It suits you very well. Very beautiful."
    bs "Sometimes you can be such a charmer!"
    scene basement 9am 022l
    bs "And look at these cool boots."
    bs "With these ornaments."
    pov "Aren't those pants a little bit to low-cut?"
    scene basement 9am 023l
    bs "<giggle> I'm surprised you're complaining."
    pov "What?"
    bs "You're a boy. Don't you like it?"
    pov "Haha, so you want me to stare?"
    scene basement 9am 024l
    if inc == True:
        bs "Yes, this time you're allowed, little brother."
    else:
        bs "Yes, this time you're allowed, [pov]."
    pov "And how did I earn this privilege?"
    bs "You brought me to this place I wanted to for so long."
    pov "Oh, but not everything here could be good."
    scene basement 9am 025l
    bs "What do you mean?"
    pov "You saw the kinky stuff in the corner?"
    bs "Yes, I didn't know about that, but I had my thoughts."
    pov "Maybe I'm a little afraid that I had to share you?"
    scene basement 9am 026l
    bs "Oh, you're so cute."
    pov "Are you flirting with me?"
    bs "<giggle>"
    pov "{i}What's gotten into her? Is she so thankful that I granted her wish as the only one?{/i}"
    scene basement 9am 027l
    bs "Oh?"
    pov "So you found the secret why the basement is needed."
    bs "These small pills laying on the table?"
    pov "Yes."
    scene basement 9am 028l
    bs "But they look like candy?"
    pov "Please don't touch them."
    bs "Why? Are they dangerous?"
    pov "Hm... Not really, but I need to tell you about them."
    scene basement 9am 029l
    bs "These are drugs? Aren't they?"
    pov "Yes, but they give you a special kick."
    bs "Then why are they bad? <giggle>"
    pov "These are sex-drugs."
    scene basement 9am 030l
    bs "Roofies?"
    pov "Thank god no. But they boost the sex-drive of women and that's why they're so popular."
    bs "And the gang sell them?"
    pov "Yes and sometimes they use it down here and that's why the kinky corner is there."
    if inc == True:
        bs "Even mom and dad?"
    else:
        bs "Even my mom and my dad?"
    pov "Yes..."
    scene basement 9am 031l
    pov "And that's also the reason why they won't let you come down here."
    bs "And they have bad side effects?"
    pov "No, surprisingly not. Maybe you can get addicted to it, and you could crave for sex, I'm not sure of that."
    scene basement 9am 032l
    bs "These little pills will get me horny in no time?"
    pov "Yes and normally I wouldn't say this, but I'm not sure if I want you to get addicted to it, haha."
    bs "Have you tried?"
    pov "They only work on women, we men have our all time sex-drive, haha."
    bs "So only for us women."
    scene basement 9am 033l
    pov "What...?"
    bs "Hmm..."
    pov "What are you doing? Didn't you hear what my words?"
    scene basement 9am 034l
    bs "<giggle>"
    pov "When you swallow that you'll get instantly horny."
    bs "Hm..."
    pov "So you can stop joking around."
    scene basement 9am 035l
    bs "<gulp>"
    pov "..."
    pov "Why?"
    scene basement 9am 036l
    bs "You still don't get it?"
    pov "Hmm..."
    bs "We're all alone down here and I took a sex-drug to get horny."
    pov "<gulp>"
    scene basement 9am 037l
    bs "I want to know what it can do and I'm here with the right person to test it."
    bs "You fulfilled my wish and so I'll thank you for that and you're right I'll have my fun too."
    bs "<giggle>"
    pov "So you want to make out with me?"
    if inc == True:
        bs "Yes, brother!"
    else:
        bs "Yes, [pov]!"
    scene basement 9am 038l
    bs "I'll let you choose how you want to please me, <giggle>"
    bs "But please don't overdo it."
    pov "I'll be a gentleman until you scream, haha."
    pov "{i}So, how should I please her?{/i}"
    call screen casbasementlovechoose

screen casbasementlovechoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1512 ypos 290 action (Hide ('casbasementlovechoose'), Jump('casbasementlovekiss')) hovered tt.Action ("Kiss her") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1512 ypos 707 action (Hide ('casbasementlovechoose'), Jump('casbasementlovetits')) hovered tt.Action ("Play with her tits") focus_mask True


    frame:
        xalign .5
        text tt.value


label casbasementlovekiss:
    pov "I know exactly what you like."
    scene basement 9am 039lk
    bs "Huh?"
    pov "<kiss>"
    bs "Hmm..."
    "You french kiss her."
    bs "<giggle>"
    scene basement 9am 040lk
    "You continue to play with her tongue."
    bs "Hmm...!"
    pov "<kiss> <lick>"
    scene basement 9am 041lk
    bs "Hah... Hnng..."
    pov "You like it so much. Getting held and kissed, playing with your tongue!"
    bs "Yes... you're right."
    pov "<lick> <kiss>"
    bs "Hah, I'm feeling so hot."
    pov "It was your choice to do the drug."
    bs "Yes... hah... and it was so good."
    scene basement 9am 042lk
    bs "Hah... Hnng..."
    if inc == True:
        bs "Hold me tight, brother!"
    else:
        bs "Hold me tight, [pov]!"
    pov "Oh I won't let you go. <lick>"
    bs "Oh god? Hnng..."
    "She begins to tremble like crazy."
    pov "Oh, so the drug is that good?"
    bs "HNN... HNNG..."
    pov "{i}Did she really have an orgasm? Is the drug that good?{/i}"
    scene basement 9am 043lk
    bs "Hah... hah..."
    pov "You didn't really...?"
    bs "<giggle> You made me cum by kissing and licking."
    pov "Wow! But so you understand now that you could go crazy on them very fast."
    bs "I'm sure you had your part there also."
    pov "So maybe we could try it without the drug, maybe I can manage to do it also."
    bs "<giggle> Maybe..."
    pov "I love you [bs]."
    scene basement 9am 044lk
    bs "You're such a gentleman. Didn't take advantage of me in this situation."
    pov "Hmm... I made you cum?"
    bs "But you hold back like I asked."
    pov "{i}I don't get it. Or does she mean that I pleased her without taking her for my own pleasure?{/i}"
    bs "Come here [pov]. It's your turn."
    scene basement 9am 045lk
    pov "My turn...?"
    bs "Since you like my mouth and tongue so much I'll reward you with them."
    pov "Oh, you're going to...?"
    bs "Yes, and I can feel your hard dick through your pants."
    scene basement 9am 046lk
    bs "So the drug affected you too, <giggle>"
    pov "It was more your sweet taste and the cumming in my arms."
    bs "So big and hard..."
    scene basement 9am 047lk
    bs "So it's time you cum too, <giggle>"
    pov "I'm excited about your lips and your tongue."
    scene basement 9am 048lk
    bs "<lick>"
    pov "Oh yes! Amazing!"
    bs "You're burning hot."
    pov "It's your wet tongue, it's driving me crazy."
    bs "Hmm..."
    scene basement 9am 049lk
    pov "Hah..."
    bs "<lick> <suck>"
    pov "You're doing so good, It's the best reward."
    pov "{i}I didn't know that she can suck so good. Is this good or bad?{/i}"
    bs "Hmm... <slurp>"
    pov "This is too good, I'll cum soon!"
    "She starts to lick you faster."
    pov "Watch out or I'll cum in your mouth."
    bs "Hmm..."
    pov "{i}She doesn't mind? Does she want me to cum in her mouth?{/i}"
    scene basement 9am 050lk
    pov "This is too much, hnng...!"
    "You cum in her mouth."
    if inc == True:
        pov "Oh yes, big sis!"
    else:
        pov "Oh yes, [bs]!"
    bs "Hmm..."
    bs "<gulp> <gulp>"
    pov "{i}Wow, she's swallowing it.{/i}"
    scene basement 9am 051lk
    pov "You... you swallowed."
    bs "Hmm... I wanted to taste you."
    pov "And is it good?"
    bs "Yes."
    if inc == True:
        bs "You taste surprisingly good, little brother."
        pov "I still can't believe it that you sucked me off, big sis."
    else:
        bs "You taste surprisingly good, [pov]."
        pov "I still can't believe it that you sucked me off, [bs]."
    bs "<giggle> You earned it yourself, like I said before."
    pov "Maybe I can earn another one?"
    bs "Haha, maybe..."
    scene black
    "You leave the basement together."
    $ dtime += 1
    $ basecasfirst = True
    jump kitchen

label casbasementlovetits:
    pov "I'll pleasure your breasts."
    scene basement 9am 039lt
    bs "Oh so you like my big boobs?"
    pov "Oh yes, they're fantastic."
    pov "And they're so weighty in my hands."
    bs "<giggle> Is that a compliment?"
    pov "More than that, like a profession of love."
    bs "<giggle>"
    pov "Let's undress."
    scene basement 9am 040lt
    if inc == True:
        bs "Calm down brother. No need to rip this top."
    else:
        bs "Calm down [pov]. No need to rip this top."
    pov "There they are. So wonderful."
    bs "You're hands all over them."
    pov "You'll love it when I knead them."
    scene basement 9am 041lt
    bs "Hah..."
    pov "See? And your rings like to be pulled on."
    bs "Hmm..."
    if inc == True:
        pov "Your boobs are really wonderful, big sis."
    else:
        pov "Your boobs are really wonderful, [bs]."
    bs "And your kneading is feeling good."
    scene basement 9am 042lt
    bs "Hah... hnn..."
    pov "Does it feel that good?"
    bs "You're right. With that drug the feeling is intense."
    pov "Then you'll love what I can do to your boobs."
    bs "Yes please, hah... don't stop!"
    scene basement 9am 043lt
    pov "<kiss> <suck>"
    bs "Oh my god! Yes!"
    if inc == True:
        pov "You're trembling, big sis."
    else:
        pov "You're trembling, [bs]."
    bs "I can't believe it, hah... ahhh..."
    bs "More!"
    "You bite her nipple gently."
    bs "Ahhh... hah... hnng..."
    pov "{i}Is the drug so strong that she came from playing with her tits? Amazing!{/i}"
    bs "Hmm... that was so good."
    pov "Because I love your tits, [bs]."
    scene basement 9am 045lt
    bs "You did such a good thing to my boobs you earned a reward."
    pov "A reward? Now I'm curious."
    if inc == True:
        bs "Come to me, brother."
    else:
        bs "Come to me, [pov]."
    scene basement 9am 046lt
    "She made you lay on the table."
    bs "So it's perfect. You pleasured me with my boobs and now I'll pleasure you with them."
    pov "You mean... a... boob-job?"
    bs "You already have a name for it?"
    if inc == True:
        bs "<giggle> Kinky little brother."
    else:
        bs "<giggle> Kinky [pov]."
    scene basement 9am 047lt
    bs "Your dick is burning between my boobs."
    pov "It's like a dream come true. Feeling them around it."
    bs "I want you to enjoy what's coming."
    if inc == True:
        pov "Oh, I will, big sis."
    else:
        pov "Oh, I will, [bs]."
    bs "<giggle>"
    scene basement 9am 048lt
    pov "Ohhh..."
    pov "{i}Feeling her boobs and her tongue on my dick!{/i}"
    bs "<lick>"
    pov "You're the best [bs]."
    bs "<kiss> <lick>"
    pov "I can't withstand your treatment very much longer... hah..."
    scene basement 9am 049lt
    if inc == True:
        bs "Then enjoy your orgasm like I did mine, little brother."
    else:
        bs "Then enjoy your orgasm like I did mine, [pov]."
    pov "Oh, I will, hah..."
    "She's kneading her boobs fast on your dick."
    pov "I'll spray all over you when you do that pace longer."
    bs "<giggle> So you like it that much?"
    bs "Then spray it all over the boobs you love so much."
    if inc == True:
        pov "Oh big sis!"
        scene basement 9am 050lt
        pov "Sister! Hnng!"
    else:
        pov "Oh [bs]!"
        scene basement 9am 050lt
        pov "[bs]! Hnng!"
    "She closes her eyes quickly."
    bs "Hmm..."
    pov "Ohhh..."
    scene basement 9am 051lt
    bs "So much hot sperm of you on my boobs."
    pov "Wow! You surprised me what you could do with your tits."
    bs "I'm proud to see how much you liked it <giggle>"
    pov "Maybe you can surprise me more often?"
    bs "Haha, maybe..."
    scene black
    "You leave the basement together."
    $ dtime += 1
    $ basecasfirst = True
    jump kitchen


label casbasementntr:
    hide screen locations
    scene black
    "As you enter the basement you hear voices."
    if gamemusic == True:
        stop music fadeout 2
        play music "music/NTR.mp3"
    scene basement 4pm 060ntr
    pov "{i}What is Frank doing here? And who let him in?{/i}"
    frank "Are you ready now? I can't wait all day!"
    bs "Yes, please wait a second, daddy."
    pov "{i}Daddy? What the fuck is this? A kinky role-play?{/i}"
    scene basement 4pm 061ntr
    bs "Here I am."
    bs "What's with your hand, daddy?"
    frank "That's a sign for you. Get on your knees where you belong!"
    pov "{i}So it's a kinky role-play and I'm pretty sure what she has to do when she's on her knees.{/i}"
    pov "{i}But why is she drunk and with that idiot? I don't get it? Maybe he pays her for it.{/i}"
    if hardntr == False:
        call screen casbasementntrchoose
    else:
        jump casbasementntrwatch

screen casbasementntrchoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 671 ypos 153 action (Hide ('casbasementntrchoose'), Jump('casbasementntrinterfere')) hovered tt.Action ("Stop this") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 671 ypos 326 action (Hide ('casbasementntrchoose'), Jump('casbasementntrwatch')) hovered tt.Action ("Watch them secretly") focus_mask True

    frame:
        xalign .5
        text tt.value

label casbasementntrwatch:
    pov "{i}Let's see what will happen.{/i}"
    call screen casbasementchooselike

screen casbasementchooselike():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_approve_%s.png" xpos 671 ypos 153 action (Hide ('casbasementchooselike'), Jump('casbasementapp')) hovered tt.Action ("You like NTR") focus_mask True
        imagebutton auto "gui/icons/icon_disapprove_%s.png" xpos 671 ypos 326 action (Hide ('casbasementchooselike'), Jump('casbasementdisapp')) hovered tt.Action ("You don't like NTR") focus_mask True


    frame:
        xalign .5
        text tt.value

label casbasementdisapp:
    $ ntrhatecas = True
    jump casbasementapp

label casbasementapp:
    scene basement 4pm 062ntr
    bs "Like this daddy? Let me prove to you what I can do."
    frank "I heard you can suck very good. So let's see."
    if ntrhatecas == True:
        pov "{i}What? He can't be serious!{/i}"
    else:
        pov "{i}What? Now I'm curious.{/i}"
    frank "Come here little minx."
    bs "Yes daddy."
    scene basement 4pm 063ntr
    bs "Hmm... <suck>"
    frank "Oh, not bad."
    if ntrhatecas == True:
        pov "{i}I can't believe it! He must pay her and a lot. This fat prick.{/i}"
    else:
        pov "{i}Ha. She won't waste time.{/i}"
    scene basement 4pm 064ntr
    frank "Good, work on my dick."
    bs "Hnng... <suck>"
    frank "Getting drunk and sucking cocks! You're favourite hobbies, haha!"
    bs "Hm... hnn..."
    if ntrhatecas == True:
        if inc == True:
            pov "{i}What an asshole. Doing this with my sister.{/i}"
        else:
            pov "{i}What an asshole. Doing this with her.{/i}"
    else:
        pov "{i}She seems to love to get humiliated by him.{/i}"
    frank "I'll help you!"
    scene basement 4pm 065ntr
    bs "Hnng...! Hmm...!"
    frank "Now it's much better!"
    pov "{i}He's fucking her mouth.{/i}"
    frank "I'm close! Drink what your daddy gives you!"
    bs "Hmm..."
    frank "Argh! Yes! YES!"
    bs "Hnng... <gulp> <gulp>"
    if ntrhatecas == True:
        pov "{i}He forced her to swallow it. He must pay for this.{/i}"
    else:
        pov "{i}He forced her to swallow it. And I bet she was a good girl and swallowed it all.{/i}"
    scene basement 4pm 067ntr
    bs "See? I swallowed all, daddy!"
    frank "Not all. My precious cum dripping out of your mouth."
    bs "There was so much."
    frank "I don't care! Next time you'll swallow all or you'll get a hard spanking!"
    if ntrhatecas == True:
        pov "{i}He's threating her. Now she'll get furious!{/i}"
    bs "OK, I can do better, daddy."
    scene basement 4pm 068ntr
    bs "Oh why is everything spinning around?"
    frank "Because you drank too much, doll!"
    bs "Help me daddy..."
    frank "You have to stop drinking that much."
    scene basement 4pm 070ntr
    frank "Sweet dreams, little minx."
    bs "Hnn..."
    frank "Always drunk... disgusting..."
    if ntrhatecas == True:
        pov "{i}He used her and now he's going. What a damn asshole!{/i}"
    scene basement 4pm 071ntr
    if inc == True:
        pov "Hey, big sis, wake up."
        bs "Hnn..."
        pov "Sis... SISTER, WAKE UP!"
    else:
        pov "Hey, [bs], wake up."
        bs "Hnn..."
        pov "[bs]... WAKE UP!"
    pov "{i}Damn there is no use. She's to drunk.{/i}"
    pov "{i}But I need to get her out of here. When she got found like that...{/i}"
    if ntrhatecas == True:
        pov "{i}Argh! That prick used her and all I can do is clean up.{/i}"
    scene black
    "You bring her back to her room."
    $ dtime += 1
    $ ntrhatecas = False
    $ casbasentrevent = True
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump kitchen


label casbasementntrinterfere:
    pov "{i}I won't allow this!{/i}"
    "You show yourself."
    scene basement 4pm 062sntr
    if inc == True:
        bs "Oh hey, little brother."
    else:
        pov "Oh hey, [pov]."
    frank "You...!"
    pov "Yes! And I'll put a stop on this. Or do you think it's okay to take advantage of her while she's drunk?"
    bs "But I want him to do this. He's my daddy."
    pov "Stop this shit, [bs]."
    frank "I see, I'm not wanted anymore. I'll go."
    if inc == True:
        bs "Why you're so mad, brother?"
    else:
        bs "Why you're so mad, [pov]?"
    pov "Enough. Also you shouldn't be here and especially not drunk."
    bs "But..."
    scene black
    "After Frank has left you bring [bs] to her room, so she can sleep her drunkenness off."
    $ dtime += 1
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    $ casbasentrevent = True
    jump kitchen


label temp:
    hide screen locations
    $ basealefirst = True
    scene basement 4pm 010
    pov "Look, we made it."
    ls "The basement. The forbidden place. I'm excited!"
    pov "I wonder what they're doing down there?"
    ls "Let's see!"
    scene basement 4pm 011
    ls "That's so much alcohol!"
    pov "Please be careful and silent [ls]. We shouldn't get caught here."
    ls "So many drinks..."
    pov "..."
    scene basement 4pm 012
    ls "But I won't drink it or I'll get stupid like you, dummy!"
    pov "I'm not like that when I'm drunk!"
    ls "Haha, you remember the time 4 years ago..."
    pov "... You've never drunk alcohol, have you?"
    ls "No, I'm not stupid, haha..."
    scene basement 4pm 013
    ls "Look! Is that candy?"
    pov "{i}Candy down here...? Laying open on a table?{/i}"
    pov "Wait, let me see."
    scene basement 4pm 014
    ls "Let me have it!"
    scene basement 4pm 015
    pov "Stop!"
    with vpunch
    "You slap her hand."
    scene basement 4pm 016
    ls "Ouch! Why did you do that?"
    pov "To prevent you from eating it. We don't know what it is, but it's not candy."
    ls "But it looks like candy?"
    pov "We don't know it for sure!"
    if adatekiss == True and lilsislove >= 30:
        call screen base4lscandy
    else:
        jump base4p2

screen base4lscandy():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_love_%s.png" xpos 1170 ypos 95 action (Hide('base4lscandy'), Jump('base4kiss')) hovered tt.Action ("Kiss her [lv1]") focus_mask True
        imagebutton auto "gui/icons/icon_abort_%s.png" xpos 569 ypos 95 action (Hide('base4lscandy'), Jump('base4p2')) hovered tt.Action ("Don't kiss her") focus_mask True
        frame:
            xalign .5
            text tt.value

label base4kiss:
    scene basement 4pm 017k
    $ lilsislove += 1
    pov "<kiss>"
    ls "Hnng...?"
    scene basement 4pm 017k1
    ls "Hmm..."
    "You kiss her longer."
    ls "<kiss>"
    scene basement 4pm 017k2
    ls "Why did you kiss me?"
    pov "To show you that I'm not mad at you."
    pov "But please don't take that \"candy\" any more."
    if inc == True:
        ls "Ok, big brother. <giggle>"
    else:
        ls "Ok, [pov]. <giggle>"
    jump base4p2


label base4p2:
    scene basement 4pm 018
    ls "And what's in here?"
    ls "Oh, just a toilet."
    pov "Let me see too."
    scene basement 4pm 019
    pov "Damn, that's dirty."
    ls "Look! That's interesting..."
    scene basement 4pm 020
    pov "{i}What did she find now?{/i}"
    ls "But why is this here?"
    pov "Let me see."
    scene basement 4pm 021
    pov "{i}A changing room? What are they doing here?{/i}"
    ls "Ugh!"
    ls "<giggle>"
    pov "So you have your fun here?"
    if inc == True:
        ls "I'm just wondering why mom forbid me to go in here?"
    else:
        ls "I'm just wondering why my mom forbid me to go in here?"
    scene basement 4pm 022
    ls "And what's with that?"
    pov "{i}Damn, how does she get there so fast?{/i}"
    pov "That's a vibrator. You know what that is?"
    ls "I know what a vibrator is. But why is it so big?"
    scene basement 4pm 023
    pov "Because some people like to stick bigger things in them?"
    ls "But... this one... And why is it here?"
    pov "I don't know, but maybe we can find out?"
    ls "Hnn..."
    scene basement 4pm 024
    ls "And what are these? I never saw something like this."
    pov "Well..."
    ls "They look like instruments of torture."
    pov "{i}Well, it's something like that, haha.{/i}"
    pov "It's something for you."
    scene basement 4pm 025
    ls "For me?"
    pov "Yes, when you're bad you come in here and get tickled to death, haha."
    ls "<giggle>"
    ls "I know you're lying, so what are they for?"
    pov "They're for sex. The woman is tied up there and the man can fuck her."
    scene basement 4pm 026
    ls "For sex? Torture sex?"
    pov "More submissive sex. Some people like that."
    if inc == True:
        ls "I'm so confused, big brother. Why are they here?"
    else:
        ls "I'm so confused, [pov]. Why are they here?"
    pov "I..."
    pov "Oh, there's someone coming. Let's hide quickly."
    if NTR == True and lilsisrelationship <= 5 and davidemeet == True and davidedead == False:
        jump base4ntr
    scene black
    "You both hide behind the bar."
    scene basement 4pm 031
    ls "Ssshhh..."
    pov "{i}I wonder who's that. I always thought they only came down here in the late evenings.{/i}"
    "You decide to take a peek."
    scene basement 4pm 032
    if inc == True:
        pov "{i}It's mom.{/i}"
    else:
        pov "{i}It's [mother].{/i}"
    pov "{i}And she looks so relaxed.{/i}"
    mom "Hmm... <hum>"
    scene basement 4pm 033
    mom "<hum>"
    ls "<whisper> Why is she here?"
    pov "<whisper> I don't know..."
    mom "Lalala..."
    scene basement 4pm 034
    ls "<whisper> Huh?"
    "You two are hearing a louder buzzing sound."
    "<buzz>"
    ls "<whisper> What is that?"
    pov "<whisper> Let's take a peek, but very carefully."
    ls "<whisper> Ok."
    scene basement 4pm 035
    ls "<whisper> Slowly..."
    pov "{i}Hmm... that must be an excited adventure for her...{/i}"
    if inc == True:
        pov "{i}But now let's see what mom's doing.{/i}"
    else:
        pov "{i}But now let's see what [mother]'s doing.{/i}"
    scene basement 4pm 036
    "<buzz>"
    mom "Hmm... hah... yes!"
    pov "{i}Damn, she's riding on that Sybian and fucking herself.{/i}"
    ls "<whisper> Hnng..."
    scene basement 4pm 038
    pov "{i}Why is she looking so sad?{/i}"
    pov "<whisper> What's wrong?"
    ls "<whisper> Don't you see what she's doing?"
    pov "..."
    if inc == True:
        ls "<whisper> Mom is masturbating with that thing..."
    else:
        ls "<whisper> My mom is masturbating with that thing..."
    pov "<whisper> And so what?"
    mom "Hah... yes... harder..."
    ls "<whisper> She's doing it like a slut..."
    pov "{i}Wow, oh shit...{/i}"
    pov "<whisper> Come..."
    scene basement 4pm 039
    ls "<whisper> Huh? What are you up to?"
    pov "<whisper> You need to relax."
    call screen base4lshide

screen base4lshide():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_love_%s.png" xpos 1170 ypos 95 action (Hide('base4lshide'), Jump('base4lscalm')) hovered tt.Action ("Calm her down [lv1]") focus_mask True
        imagebutton auto "gui/icons/icon_corruption_%s.png" xpos 569 ypos 95 action (Hide('base4lshide'), Jump('base4lsuse')) hovered tt.Action ("Use this situation [cr1]") focus_mask True
        frame:
            xalign .5
            text tt.value

label base4lscalm:
    scene basement 4pm 039c
    $ lilsislove += 1
    if inc == True:
        pov "<whisper> Calm down, lil sis. It's not your fault."
    else:
        pov "<whisper>Calm down [ls]. It's not your fault."
    pov "<whisper> She may love to do it but it doesn't make you a slut."
    mom "Hah... hnng..."
    "<buzz>"
    if inc == True:
        ls "But she's our mom."
    else:
        ls "But she's my mom."
    pov "<whisper> Sshhh..."
    scene basement 4pm 040
    pov "<whisper> Come here. I won't allow you to become a slut."
    ls "<whisper> But..."
    mom "Aaah... hah... more!"
    if inc == True:
        pov "<whisper> You're my little sister and I love you, so don't worry."
    else:
        pov "<whisper> I know you all my life and I love you, so don't worry."
    pov "<whisper> And I'm the last one that would judge you."
    ls "<whisper> But why is she doing it?"
    scene basement 4pm 041
    pov "<whisper> I don't know [ls]. That's something we need to find out."
    pov "<kiss>"
    pov "<whisper> Also it's pretty normal to have such feelings sometimes."
    ls "<whisper> Hmm..."
    "<buzz>"
    mom "Yes! Hah... Aaahh... Hnng..."
    scene basement 4pm 042
    ls "<kiss>"
    pov "{i}Huh? She's kissing me. And it feels different then the times before.{/i}"
    ls "<whisper> Hmm..."
    mom "Hnn... hnn..."
    scene basement 4pm 043
    if inc == True:
        pov "{i}Oh my god. My little sister took advantage and is french kissing me.{/i}"
    else:
        pov "{i}Oh my god. [ls] took advantage and is french kissing me.{/i}"
    ls "<lick> <kiss>"
    if inc == True:
        pov "{i}And mom is masturbating at the same time too. This is heaven.{/i}"
    else:
        pov "{i}And [mother] is masturbating at the same time too. This is heaven.{/i}"
    mom "Hah... hah... hah..."
    pov "{i}I wonder what I did to earn this pleasure? Because I was so nice to her?{/i}"
    if inc == True:
        pov "{i}Or is she getting horny by the moans of mom?{/i}"
    else:
        pov "{i}Or is she getting horny by the moans of her mother?{/i}"
    scene basement 4pm 044
    ls "Hmm..."
    ls "<kiss> <lick>"
    pov "{i}Now it's my time to just enjoy it.{/i}"
    mom "Oh yes... oh yes..."
    if inc == True:
        pov "{i}But lil sis is kissing me really eager. That's a little surprising.{/i}"
    else:
        pov "{i}But [ls] is kissing me really eager. That's a little surprising.{/i}"
    scene basement 4pm 045
    ls "<giggle>"
    pov "{i}Damn, she looks so cute right now.{/i}"
    "You stare in each others eyes."
    mom "Hah... hah... AAAHHHH...!"
    pov "{i}So she had her fun too.{/i}"
    ls "<whisper> Huh?"
    "The buzzing sound stops and it goes silent."
    scene basement 4pm 048
    if inc == True:
        ls "<whisper> Mom is leaving."
    else:
        ls "<whisper> My mother is leaving."
    "You got the bad feeling that [ls] was overwhelmed by the situation and decide to stop it here."
    scene basement 4pm 045
    pov "Let's go back. The way is clear."
    ls "Did I do something wrong."
    pov "No. It was nice, but we will have more time later."
    ls "<giggle> You want more of me."
    if inc == True:
        pov "Yes, because I love you, lil sis."
    else:
        pov "Yes, because I love you, [ls]."
    ls "<giggle>"
    scene black
    $ lilsisrelationship += 1
    "You leave the basement together."
    $ b4ralove = True
    $ dtime += 1
    jump frontdoor

label base4lsuse:
    pov "<whisper> I know you're right, but we have to stay silent."
    $ lilsiscorruption += 1
    ls "<whisper> Hnn..."
    pov "<whisper> She's a slut and I'm pretty sure she won't be the only one in this family."
    "<buzz>"
    mom "Hah... aahhh..."
    scene basement 4pm 040c
    ls "<whisper> What are you doing?"
    pov "<whisper> I'll show you that I'm right. That you're a slut too, you'll get horny from her moanings."
    mom "Hah... hah... hah..."
    ls "<whisper> But..."
    scene basement 4pm 041c
    pov "<whisper> See? I was right. You nipples are damn stiff."
    ls "<whisper> No..."
    "<buzz>"
    mom "Hnng... aahh..."
    pov "<whisper> I have to say sorry, but most probably you'll become a slut too."
    ls "<whisper> Hnng..."
    scene basement 4pm 042c
    pov "<whisper> See? I touch you and you're getting horny!"
    ls "<whisper> Hnng... I'm sorry..."
    pov "<whisper> There is no need to be. Just give in to your feelings."
    ls "<whisper> But... I don't want to be a slut."
    mom "Hah... aaahh... yes!"
    scene basement 4pm 043c
    pov "<whisper> Relax [ls]. You can't deny it. It's your nature."
    ls "<whisper> Hnn..."
    if inc == True:
        pov "<whisper> But you're my little sister and I won't tell anyone. It'll be our secret."
        mom "Hah... hah... hah..."
        pov "<whisper> See? You can have fun as mom does."
    else:
        pov "<whisper> But I know you all your life and I won't tell anyone. It'll be our secret."
        mom "Hah... hah... hah..."
        pov "<whisper> See? You can have fun as your mom does."
    ls "<whisper> But..."
    scene basement 4pm 044c
    ls "<whisper> Hnng...!"
    pov "<whisper> Stop complaining! You're already wet."
    if inc == True:
        pov "<whisper> So trust your big brother."
    else:
        pov "<whisper> So trust me."
    ls "<whisper> Hmm... if you say so..."
    "<buzz>"
    mom "Harder, hah.. ahh..."
    pov "<whisper> Just give in already..."
    if inc == True:
        ls "<whisper> Hnng... your fingers, big brother."
    else:
        ls "<whisper> Hnng... your fingers, [pov]."
    scene basement 4pm 045c
    pov "<whisper> Good, no fighting back anymore."
    ls "<whisper> Hnng... hah..."
    pov "<whisper> But you must admit it to yourself or you won't get over it."
    mom "Aaahh... aahhh..."
    ls "<whisper> Admit... hnn... it?"
    pov "<whisper> Yes. Admit it to me and you'll feel much better."
    ls "<whisper> Hnn... but..."
    pov "<whisper> Admit it!"
    if inc == True:
        ls "Big brother... I'm... I'm a..."
    else:
        ls "[pov]... I'm... I'm a..."
    pov "<whisper> Huh?"
    "The buzzing sound stops and it's now silent."
    scene basement 4pm 048
    if inc == True:
        ls "<whisper> Mom is leaving."
    else:
        ls "<whisper> My mother is leaving."
    scene basement 4pm 045c
    pov "{i}Damn, she almost said it.{/i}"
    if inc == True:
        ls "Mom is gone... please stop now."
    else:
        ls "My mom is gone... please stop now."
    pov "Why? You still need to admit it. And you're enjoying it also."
    if inc == True:
        ls "No! Please brother."
    else:
        ls "No! Please [pov]."
    pov "{i}Damn!{/i}"
    scene black
    "She frees herself and runs back through the tunnel."
    pov "{i}But, I'll get her her to admit it soon.{/i}"
    $ lilsisrelationship += 1
    "You also go back."
    $ b4racor = True
    $ dtime += 1
    jump frontdoor

label base4ntr:
    scene black
    $ basement4pmntrfirst = True
    "You hide behind the couch, but [ls] stays behind the bar."
    "Someone enter the room."
    if gamemusic == True:
        stop music fadeout 2
        play music "music/NTR.mp3"
    scene basement 4pm 031n
    pov "{i}It's Davide. What he's doing here at this time?{/i}"
    scene basement 4pm 032n
    if inc == True:
        pov "{i}Oh shit, he's doing something at the bar. I hope he doesn't find lil sis.{/i}"
    else:
        pov "{i}Oh shit, he's doing something at the bar. I hope he doesn't find [ls].{/i}"
    scene basement 4pm 033n
    ls "Buh!"
    davide "Huh?"
    pov "{i}What's she doing?{/i}"
    davide "Hahaha, what a nice surprise."
    scene basement 4pm 034n
    davide "How did you get in here [ls]?"
    ls "Oh you remember me? <giggle>"
    davide "How could I forget such a hot chick!"
    ls "I found a way in to the basement."
    scene basement 4pm 035n
    davide "So you came here to find out the secrets of the basement?"
    ls "Yes..."
    if davidemeetint == True:
        davide "And now you're alone with a black man. Like in one of your fantasies?"
        ls "Hnn..."
    else:
        davide "And now you're alone here with me. I have an idea what we can do."
    pov "{i}Damn, he's trying to get on with her.{/i}"
    davide "So come here."
    scene basement 4pm 036n
    ls "Huh?"
    davide "Holding such a beauty like you in my arms. This must be my lucky day!"
    ls "<giggle>"
    call screen base4ntrch

screen base4ntrch():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 869 ypos 95 action (Hide('base4ntrch'), Jump('base4ntrin')) hovered tt.Action ("Interfere") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1170 ypos 95 action (Hide('base4ntrch'), Jump('base4ntrpa')) hovered tt.Action ("Show yourself") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 569 ypos 95 action (Hide('base4ntrch'), Jump('base4ntrwa')) hovered tt.Action ("Just watch") focus_mask True
        frame:
            xalign .5
            text tt.value

label base4ntrin:
    pov "{i}I need to do something. I don't like the way this could go.{/i}"
    "You reveal yourself."
    pov "Hey!"
    scene basement 4pm 037n
    davide "Huh?"
    if inc == True:
        ls "Hey, big brother."
    else:
        ls "Hey, [pov]."
    davide "You're here too."
    pov "Yes I am."
    pov "And I don't like what I see, so we're leaving now."
    scene basement 4pm 038ni
    pov "Come on [ls], let's go."
    ls "But I like..."
    pov "Now!"
    davide "When she wants to stay with me?"
    pov "We found this place and maybe we came down here even if it's forbidden."
    pov "But I'm sure you can think about what will happen if [mother] finds out that [ls] was here with you!"
    davide "Maybe I don't care!"
    pov "I can see you're bluffing. [ls], come now!"
    scene basement 4pm 039ni
    ls "Bye Davide."
    davide "We'll meet soon, honey."
    pov "Oh, I don't think so."
    scene basement 4pm 040ni
    davide "You'll get yourself into more and more trouble. If you don't support the gang."
    pov "I don't care. And I'll make sure that you won't get your hands on her."
    davide "We'll see. This isn't over."
    scene black
    if inc == True:
        "You and your little sister leave the basement."
    else:
        "You and [ls] leave the basement."
    $ dtime += 1
    $ b4rantrdavidei = True
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump frontdoor

label base4ntrpa:
    pov "{i}I want him to know that I'm here too.{/i}"
    "You reveal yourself."
    pov "Hey!"
    scene basement 4pm 037n
    davide "Huh?"
    if inc == True:
        ls "Hey, big brother."
    else:
        ls "Hey, [pov]."
    davide "You're here too."
    pov "Yes I am."
    pov "You two having fun?"
    scene basement 4pm 038na
    davide "Yes I'd have to thank you for bringing this cutie here."
    ls "<giggle>"
    if inc == True:
        pov "So you like him too, lil sis?"
    else:
        pov "So you like him too, [ls]?"
    ls "He's so strong. <giggle>"
    davide "And you're so pure, like white chocolate!"
    davide "And it's about time we get to know each other better."
    scene basement 4pm 039na
    ls "Hmm...?"
    davide "<kiss>"
    pov "Ha, another way to get to know someone better."
    pov "{i}He surprised her with a french kiss. And she seems to like it.{/i}"
    scene basement 4pm 040na
    davide "That has to be done!"
    ls "<giggle>"
    davide "You should come by more often, maybe we find you a girl too [pov]."
    pov "We'll see. But a nice way to get to know someone, haha."
    davide "Yes, you have to do it fast and direct!"
    ls "I can still taste your saliva, <giggle>"
    scene basement 4pm 041na
    davide "And you'll soon taste some other stuff."
    if davidemeetint == True:
        davide "And you have some special interest in black dicks, I'll teach you much."
    ls "Hnn..."
    davide "Your holes need to get plugged soon, so you'll be a happy girlfriend!"
    pov "Haha... damn!"
    ls "Hnn..."
    pov "{i}She's so confused.{/i}"
    davide "And so..."
    scene basement 4pm 042na
    davide "Damn, something is unlocking the basement door."
    ls "Plugged..."
    davide "You should leave now. It's better if we keep this hidden for now!"
    pov "Haha, fearing [mother]?"
    davide "I won't risk my new holes, haha."
    ls "His holes... <giggle>"
    scene basement 4pm 043na
    davide "I'll give you some time to leave unseen."
    davide "Make sure you come here again at night time so that I can teach you more!"
    pov "Come on let's go, [ls]."
    ls "He wants me to be his girlfriend..."
    pov "Haha, relax. Some other time."
    scene black
    "You leave the basement together."
    $ dtime += 1
    $ b4rantrdavidey = True
    $ ntrloveale = True
    $ davidealexisfriends = True
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump frontdoor

label base4ntrwa:
    pov "{i}It's better that he doesn't know that I'm here.{/i}"
    pov "{i}So I can see what she was up to with her revealing.{/i}"
    scene basement 4pm 037nn
    ls "Hmm...?"
    davide "<kiss>"
    pov "{i}Oh shit!{/i}"
    call screen base4ntrpr

screen base4ntrpr():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_approve_%s.png" xpos 1170 ypos 95 action (Hide('base4ntrpr'), Jump('base4ntrap')) hovered tt.Action ("Let her have her fun") focus_mask True
        imagebutton auto "gui/icons/icon_disapprove_%s.png" xpos 569 ypos 95 action (Hide('base4ntrpr'), Jump('base4ntrdis')) hovered tt.Action ("I don't like this") focus_mask True
        frame:
            xalign .5
            text tt.value

label base4ntrap:
    $ base4ntrlike = True
    jump base4ntrdis

label base4ntrdis:
    scene basement 4pm 038nn
    pov "{i}She seems to enjoy getting kissed by him.{/i}"
    if base4ntrlike == False:
        $ b4rantrdaviden = True
        if inc == True:
            pov "{i}That damn asshole. Making out with my little sister.{/i}"
        else:
            pov "{i}That damn asshole. Making out with [ls].{/i}"
    ls "Hnng..."
    pov "{i}And she's totally into it. Getting french kissed.{/i}"
    scene basement 4pm 039nn
    ls "Hah... hah..."
    davide "You're mine now. I conquered you with this kiss and marked you with my salvia!"
    ls "I... was... hah... conquered..."
    if base4ntrlike == True:
        $ b4rantrdavidey = True
        pov "{i}Damn, what an aggressive hit on her.{/i}"
    else:
        pov "{i} Don't believe this shit! He's tricking you.{/i}"
    davide "Yeah, accept it, cutie!"
    ls "I'm... hah... yours..."
    if base4ntrlike == False:
        pov "{i}Nooo!{/i}"
    davide "Good girl!"
    scene basement 4pm 040nn
    ls "Yes, I'm a good girl. <giggle>"
    davide "Oh it wasn't supposed to go this way, but you'll learn that soon."
    if base4ntrlike == False:
        if inc == True:
            pov "{i}No! Stop corrupting my little sister!{/i}"
        else:
            pov "{i}No! Stop corrupting her!{/i}"
    else:
        pov "{i}She seem to like this game.{/i}"
    davide "So then you're mine now, I should start teaching you, shouldn't I?"
    ls "<giggle> And what's my first lesson?"
    if base4ntrlike == False:
        pov "{i}Don't you dare, motherfucker! I'll get my revenge!{/i}"
    scene basement 4pm 041nn
    davide "To don't waste time you'll meet the toy that'll plug your holes soon!"
    if davidemeetint == True:
        davide "And because I know that you've a weakness for me it'll make you very happy!"
    ls "Your toy?"
    if base4ntrlike == True:
        pov "{i}Haha, she's so damn innocent.{/i}"
    else:
        pov "{i}No, she's innocent. Don't take it away!{/i}"
    scene basement 4pm 042nn
    davide "Yes my dick that'll conquer each of your holes and mark them as mine!"
    ls "Ohhh..."
    davide "You're eager to see it. You look very interested, aren't you?"
    if base4ntrlike == False:
        pov "{i}I'll kill you, you damn asshole!{/i}"
    scene basement 4pm 043nn
    ls "Oh my god! It's so big!"
    ls "<biting her finger>"
    davide "Then go on and explore it more. You should know what will enter you!"
    if base4ntrlike == False:
        pov "{i}Stop...{/i}"
    ls "But it's so big. Wouldn't it hurt?"
    davide "The first time maybe, until your holes are widen enough for it."
    davide "But the sooner I plug you, you'll get addicted."
    ls "Addicted? <giggle>"
    scene basement 4pm 043nnn
    ls "Oh..."
    davide "What's wrong?"
    ls "It's so hard and hot!"
    davide "Yes because it wants to enter you badly."
    if base4ntrlike == False:
        pov "{i}I can't endure this anymore! But I can't leave her alone with him either!{/i}"
    scene basement 4pm 044nn
    ls "I'm a little bit scared."
    davide "Of my big cock, haha?"
    ls "It'll never fit inside me..."
    davide "Oh it will. It may not be easy for you, but as a good girl you must endure that."
    if base4ntrlike == False:
        pov "{i}Grrr...{/i}"
    ls "Then I must try to be... a good girl..."
    scene basement 4pm 045nn
    davide "Oh shit..."
    ls "What...?"
    davide "Someone is unlocking the basement door!"
    ls "Ohh..."
    if base4ntrlike == False:
        pov "{i}Thank god!{/i}"
    else:
        pov "{i}Damn. I would watch this.{/i}"
    scene basement 4pm 046nn
    davide "I'll go and give you some time to leave. It's better when no one knows that you're here."
    davide "Make sure you come here again at night time so that I can teach you more!"
    ls "Ok. I can do that!"
    davide "See you then, my girl."
    ls "I hope so, my boy. <giggle>"
    if base4ntrlike == False:
        pov "{i}That's not good. She doesn't understand the seriousness!{/i}"
    scene basement 4pm 047nn
    if inc == True:
        "Davide goes to the stairs and your little sister leaves the basement."
    else:
        "Davide goes to the stairs and [ls] leaves the basement."
    pov "{i}Why did she do that? She knew that I was here too?{/i}"
    scene black
    "After Davide went upstairs you leave the basement too."
    if inc == True:
        "Your little sister wasn't seen anymore."
    else:
        "[ls] wasn't seen anymore."
    $ dtime += 1
    if base4ntrlike == True:
        $ ntrloveale = True
        $ ntrhateale = False
    else:
        $ ntrhateale = True
        $ ntrloveale = False
    $ davidealexisfriends = True
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump frontdoor



label basementlook:
    hide screen locations
    scene black
    pov "{i}There is no use. I can't see anything.{/i}"
    jump basement

label basementopen:
    hide screen locations
    scene intro 071
    if NTR == True:
        pov "{i}Damn, locked again. I must get in there to find out what they're doing down there.{/i}"
    else:
        pov "{i}It's locked. But why? Are they hiding something down there?{/i}"
    jump basement

label basementtalk:
    hide screen locations
    if inc == True:
        pov "[mom]? Are you down there?"
    else:
        pov "[mother]? Are you down there?"
    mom "Yes honey. I'm in the basement."
    pov "Can you let me in? I want to see the basement too."
    mom "No! Sorry! But it's the gangs hideout."
    mom "Only for gang members!"
    pov "What the fuck?"
    if inc == True:
        mom "Sorry [pov], but I had to promise your dad. Your sisters aren't allowed down there either."
    else:
        mom "Sorry [pov], but I had to promise Bruce. My daughters aren't allowed down there either."
    if NTR == True:
        pov "{i}But I have to get down there to find out what happened there the night I came home.{/i}"
    pov "{i}But I want to know about that hideout.{/i}"
    $ momrelationship += 1
    $ dtime += 1
    $ basementnicole4pmfirst = True
    jump basement


label base10pmnic:
    hide screen locations
    $ basenicfirst = True
    scene basement 10pm 040
    "As you enter the basement [mother] is already waiting for you."
    mom "There you are. I have something for you."
    scene basement 10pm 041
    mom "It's my favorite drink and I want you to taste it."
    pov "So you drink it only here in the basement?"
    mom "Yes, it's tasty but a little strong and I don't want [bs] or [ls] to drink it."
    pov "Oh, I understand."
    scene basement 10pm 043
    mom "See? All blue."
    pov "Hm..."
    pov "{i}A blue drink that has a strong effect. And she wants to drink again.{/i}"
    pov "{i}Maybe it's time to use the sex-drug on her, since we're already alone in the basement.{/i}"
    call screen base10pmnicdrug

screen base10pmnicdrug():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_corruption_%s.png" xpos 848 ypos 239 action (Hide ('base10pmnicdrug'), Jump('base10pmnicdrugy')) hovered tt.Action ("Drug her [cr1]") focus_mask True
        imagebutton auto "gui/icons/icon_abort_%s.png" xpos 1173 ypos 239 action (Hide ('base10pmnicdrug'), Jump('base10pmnicdrugn')) hovered tt.Action ("Don't drug her") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmnicdrugy:
    $ momcorruption += 1
    $ momdrug = True
    $ momdrugfirst = True
    pov "{i}I need to test the drug on her.{/i}"
    pov "What's the name of the drink?"
    scene basement 10pm 042
    mom "Let me see."
    "You put the drug in her glass."
    pov "{i}Good and it's already dissolved because of the carbolic acid in it.{/i}"
    mom "The name is \"Blue orgasm\". And it's the best name for it."
    if inc == True:
        pov "Oh you have no idea, mom."
    else:
        pov "Oh you have no idea, [mother]."
    scene basement 10pm 044
    mom "Cheers!"
    "You taste yours too."
    pov "Hm... not bad."
    "She drank much from her glass."
    scene basement 10pm 045
    mom "Oh, so good! And your judgment?"
    pov "Yes, a little too sweet, but still okay by me."
    mom "<giggle>"
    mom "I'm glad you like it."
    scene basement 10pm 046
    mom "Huh?"
    "She drops her glass."
    pov "{i}Damn, did she catch me?{/i}"
    mom "Something is wrong?"
    if inc == True:
        pov "What's wrong mom?"
    else:
        pov "What's wrong mother?"
    scene basement 10pm 047
    mom "Oh my god! Urgh!"
    pov "Are you OK?"
    mom "My stomach..."
    scene basement 10pm 048
    mom "Excuse me [pov]!"
    pov "{i}Damn, that's a bad surprise. Maybe mixing the drug with the drink was a bad idea.{/i}"
    "She runs into the toilet."
    scene basement 10pm 049
    mom "Barf! Urgh!"
    pov "{i}Damn, really a bad decision. At least she got rid of her dress and won't ruin it.{/i}"
    if inc == True:
        pov "Are you okay, mom?"
    else:
        pov "Are you okay, [mother]?"
    pov "{i}I have to get closer, she can't hear me.{/i}"
    scene basement 10pm 050
    mom "Urgh! Urgh!"
    if inc == True:
        pov "Are you okay mom?"
        mom "Yes, I'm so sorry [pov]."
    else:
        pov "Are you okay [mother]?"
        mom "Yes, I'm so sorry [pov]."
    pov "{i}Damn, so no fun for me today...{/i}"
    pov "{i}Or I'll have a good toilet fuck with her.{/i}"
    call screen base10pmnictfchoose

screen base10pmnictfchoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_corruption_%s.png" xpos 668 ypos 260 action (Hide ('base10pmnictfchoose'), Jump('base10pmnicdrugf')) hovered tt.Action ("Take advantage and fuck her [cr1]") focus_mask True
        imagebutton auto "gui/icons/icon_abort_%s.png" xpos 1217 ypos 260 action (Hide ('base10pmnictfchoose'), Jump('base10pmnicdrugnf')) hovered tt.Action ("Leave her alone") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmnicdrugnf:
    pov "{i}No, that would be to cruel.{/i}"
    pov "Are you okay? Can I do something?"
    mom "No, it's alright [pov]. I just need some time."
    mom "And I'm really sorry! I don't know why this is happening now."
    pov "OK. Please tell me if you need something."
    mom "I will. But you can go now, I'm feeling a little uncomfortable with this situation right now."
    pov "OK. Get well."
    scene black
    "You leave the basement."
    jump basement

label base10pmnicdrugf:
    $ momcorruption += 1
    $ momtoiletfuck = True
    pov "{i}I'll have my fun with her now and she won't complain in this situation.{/i}"
    scene basement 10pm 051
    "You pull her string down."
    mom "What's happening? Something feels weird."
    if inc == True:
        pov "I don't know mom. Nothing happened."
    else:
        pov "I don't know [mother]. Nothing happened."
    mom "But... Urgh! Barf!"
    pov "{i}Good, she's distracted again.{/i}"
    scene basement 10pm 052
    "You pull your dick out."
    pov "{i}So it's my time to have fun with her now! My right as a gang member!{/i}"
    pov "{i}But which hole should I choose?{/i}"
    call screen base10pmnictfhole

screen base10pmnictfhole():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 753 ypos 699 action (Hide ('base10pmnictfhole'), Jump('base10pmnictfpussy')) hovered tt.Action ("Fuck her pussy") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1407 ypos 699 action (Hide ('base10pmnictfhole'), Jump('base10pmnictfass')) hovered tt.Action ("Fuck her ass") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmnictfass:
    pov "{i}I need to do fuck her asshole!{/i}"
    $ momtoiletfuckass = True
    jump base10pmnictfpussy

label base10pmnictfpussy:
    if momtoiletfuckass == False:
        pov "{i}I need to do fuck her pussy!{/i}"
    scene basement 10pm 053
    mom "AHH!"
    if momtoiletfuckass == False:
        pov "{i}Damn, she's so wet, I could slide so easy in her.{/i}"
    mom "What are you...?"
    scene basement 10pm 054
    mom "Are you crazy? You're fucking me."
    if inc == True:
        pov "I couldn't resist mom. I was so horny all day."
    else:
        pov "I couldn't resist [mother]. I was so horny all day."
    mom "That's no excuse. You're taking advantage of this situation!"
    pov "Yes!"
    scene basement 10pm 055
    pov "And now be a good lower gang member and enjoy the fucking!"
    mom "You can't be serious! Please stop! Urgh!"
    pov "You're getting damn tight."
    if inc == True:
        pov "You're enjoying this secretly, aren't you, mom?"
    else:
        pov "You're enjoying this secretly, aren't you, [mother]?"
    mom "You're so mean."
    pov "{i}I wonder if the rest of the drug is still working?{/i}"
    "You fuck her faster."
    mom "Hah... hah..."
    pov "As I thought. You like to be fucked this way."

    scene basement 10pm 056
    mom "Please stop. I won't get angry if you stop here, hah."
    pov "There's no way I'm stopping now. I can feel your enjoyment."
    mom "Hah, you're wrong... stop, hnn..."
    pov "{i}She's getting even more tight. She'll cum soon.{/i}"
    mom "Hah, hah, [pov]."
    scene basement 10pm 057
    mom "AAHHH! HAAAH!"
    if inc == True:
        pov "Yes cum with me, mom!"
    else:
        pov "Yes cum with me, [mother]!"
    pov "{i}I need to cum also, but where to put my sperm?{/i}"
    call screen base10pmnictfcchoose

screen base10pmnictfcchoose():
    default tt = Tooltip (" ")

    fixed:
        if momtoiletfuckass == True:
            imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1335 ypos 134 action (Hide ('base10pmnictfcchoose'), Jump('base10pmnictfcass')) hovered tt.Action ("Cum in her ass") focus_mask True
        else:
            imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1335 ypos 134 action (Hide ('base10pmnictfcchoose'), Jump('base10pmnictfcpussy')) hovered tt.Action ("Cum in her pussy") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1518 ypos 134 action (Hide ('base10pmnictfcchoose'), Jump('base10pmnictfonass')) hovered tt.Action ("Cum on her ass") focus_mask True



    frame:
        xalign .5
        text tt.value

label base10pmnictfonass:
    scene basement 10pm 058a
    if inc == True:
        pov "I'll mark you now, mom!"
    else:
        pov "I'll mark you now, [mother]!"
    pov "HNG!"
    mom "Ah, hah... hah..."
    pov "That was a good reward for being a gang member, don't you think?"
    mom "Hng... hah..."
    pov "You're still done because you came so hard, haha."
    scene basement 10pm 059a
    pov "Oh yes, I marked you good."
    mom "Hnn... Urgh!"
    jump base10pmnictfend


label base10pmnictfcass:
    scene basement 10pm 058b
    if inc == True:
        pov "Yes, take my sperm, mom!"
    else:
        pov "Yes, take my sperm, [mother]!"
    pov "HNG!"
    mom "Ah, hah... hah..."
    pov "That was a good reward for being a gang member, don't you think?"
    mom "Hng... hah..."
    pov "You're still done because you came so hard, haha."
    scene basement 10pm 059b
    pov "Oh yes, I came deep in your ass."
    mom "Hnn... Urgh!"
    jump base10pmnictfend


label base10pmnictfcpussy:
    scene basement 10pm 058b
    if inc == True:
        pov "Yes, take my seed, mom!"
    else:
        pov "Yes, take my seed, [mother]!"
    pov "HNG!"
    mom "Ah, hah... hah..."
    pov "That was a good reward for being a gang member, don't you think?"
    mom "Hng... hah..."
    pov "You're still done because you came so hard, haha."
    scene basement 10pm 059c
    pov "Oh yes, I creampied you good."
    mom "Hnn... Urgh!"
    jump base10pmnictfend

label base10pmnictfend:
    pov "{i}She's still not good, but that was good fun!{/i}"
    pov "{i}But it's better to go now, she'll get really angry when she's feeling better.{/i}"
    scene black
    "You leave the basement."
    $ momtoiletfuckass = False
    $ dtime += 1
    jump lroom


label base10pmnicdrugn:
    pov "{i}No I want to spend my time with her when she isn't drugged.{/i}"
    pov "{i}I don't need them to make her mine.{/i}"
    scene basement 10pm 044
    mom "Cheers!"
    "You taste yours."
    pov "Hm... not bad."
    "She drank much from her glass."
    scene basement 10pm 045
    mom "Oh, so good! And your judgment?"
    pov "Yes, a little sweet, but still okay by me."
    mom "<giggle>"
    mom "I'm glad you like it."
    if momcorruption >= momlove:
        jump base10pmniccor
    else:
        jump base10pmniclove


label base10pmniccor:
    pov "I have an idea. I want you to do something for me."
    scene basement 10pm 047c
    mom "Huh? And what is that?"
    pov "As a gang member now I want you to wear something nicer for me."
    mom "Wear something else?"
    pov "Oh, I'm sure you have some nice outfits in that changing room."
    scene basement 10pm 048c
    mom "But I only wear them..."
    pov "I'm a gang member now, so you can wear them when I'm around too."
    mom "But..."
    pov "Don't worry, I'll choose something hot and sexy for you!"
    mom "No, I won't..."
    pov "I know you want to, but you're just a little bit confused."
    pov "So I'll help you."
    scene basement 10pm 049c
    pov "As a higher gang member I order you to do it or I'll tell the others about your misbehavior."
    mom "You can't be serious."
    pov "Oh yes I am. Why do you still struggle about something so trivial you leave me no other choice."
    mom "Hm... I'll do it."
    pov "See? I knew you wanted it to."
    scene basement 10pm 050c
    mom "Let me see..."
    pov "Oh I found something."
    pov "I'll choose..."
    call screen base10pmniccoroutfitchoose

screen base10pmniccoroutfitchoose():
    default tt = Tooltip (" ")

    fixed:

        imagebutton auto "gui/icons/icon_red_%s.png" xpos 597 ypos 100 action (Hide ('base10pmniccoroutfitchoose'), Jump('base10pmnicred')) hovered tt.Action ("Choose this one") focus_mask True
        imagebutton auto "gui/icons/icon_school_%s.png" xpos 1297 ypos 100 action (Hide ('base10pmniccoroutfitchoose'), Jump('base10pmnicschool')) hovered tt.Action ("Choose this one") focus_mask True

    frame:
        xalign .5
        text tt.value

label base10pmnicred:
    $ base10pmnicred = True
    jump base10pmnicschool

label base10pmnicschool:
    pov "Go on, don't make me wait."
    mom "O... okay..."
    if base10pmnicred == True:
        scene basement 10pm 051cb
        mom "Are you satisfied now?"
        if inc == True:
            pov "Wow mom! You're a killer! This dress is so hot!"
        else:
            pov "Wow [mother]! You're a killer! This dress is so hot!"
        mom "Hnng..."
    else:
        scene basement 10pm 051ca
        mom "I look like a slut!"
        if inc == True:
            pov "Yes mom! But like a very sexy slut!"
        else:
            pov "Yes [mother]! But like a very sexy slut!"
        mom "Hnng..."
    pov "Come here!"
    if base10pmnicred == True:
        scene basement 10pm 052cb
    else:
        scene basement 10pm 052ca
    pov "Don't be afraid. What happens here, will stay here. I won't tell anyone, don't worry."
    mom "..."
    pov "And also I don't want the other idiots to know what fun we have here together."
    mom "Fun..."
    if inc == True:
        mom "Humiliating your mom with slutty outfits."
    else:
        mom "Humiliating me with slutty outfits."
    pov "You're not slutty, you're very sexy."
    pov "And the outfits there to wear it, so you mustn't show it to others."
    if inc == True:
        pov "So it's still in the family."
    pov "And I won't make you do anything you don't won't to do. You know that."
    pov "{i}At least for now, haha.{/i}"
    mom "Hm... maybe you aren't that wrong..."
    pov "See? And now let me see more."
    if base10pmnicred == True:
        scene basement 10pm 053cb
    else:
        scene basement 10pm 053ca
    pov "Incredible. You look so young."
    mom "..."
    if inc == True:
        pov "Your legs are very beautiful, mom."
    else:
        pov "Your legs are very beautiful, [mother]."
    if base10pmnicred == True:
        scene basement 10pm 054cb
    else:
        scene basement 10pm 054ca
    mom "Hnn..."
    pov "I would prefer a \"Thank you\" more. Come on don't be shy."
    mom "Th... thank you."
    pov "And even your beautiful tits. The outfit shows only a little of them, but enough to leave a good impression."
    mom "Isn't that a little too much..."
    pov "..."
    mom "T... thank you again."
    pov "Good girl!"
    pov "Now come sit with me."
    if base10pmnicred == True:
        scene basement 10pm 055cb
    else:
        scene basement 10pm 055ca
    pov "{i}She's still not convinced. She's sitting on a separate armchair.{/i}"
    pov "{i}Maybe I need to let her open up some more.{/i}"
    if inc == True:
        pov "Are you afraid of me, mom?"
    else:
        pov "Are you afraid of me, [mother]?"
    mom "Should I?"
    pov "No, there's no reason for that. I won't do anything bad to you with my new position."
    pov "But it's hard to withstand while you're wearing something sexy."
    if base10pmnicred == True:
        scene basement 10pm 056cb
    else:
        scene basement 10pm 056ca
    mom "Please stop saying these things."
    if inc == True:
        mom "You're still my son."
    else:
        mom "You're still the son of my best friend."
    pov "No, I can't hide the truth. And it has to be said to a beauty like you."
    mom "Hnn..."
    pov "These outfits would even be good for a date."
    mom "Hm..."
    pov "{i}Is she flustered? Maybe I'm not so wrong here.{/i}"
    pov "But you also could undress if you feel uncomfortable in this outfit."
    if base10pmnicred == True:
        scene basement 10pm 057cb
    else:
        scene basement 10pm 057ca
    mom "What?"
    pov "Haha, I'm kidding. But it was worth a try."
    mom "Stop that."
    pov "Haha, relax. But this gives me another idea."
    pov "You could dance a little for me."
    mom "What?"
    pov "Here on the table. So I can adore you in your sexy outfit."
    if base10pmnicred == True:
        scene basement 10pm 058cb
    else:
        scene basement 10pm 058ca
    mom "Hnn... I'll do it. But I'm not a stripper."
    if inc == True:
        pov "Of course, mom."
    else:
        pov "Of course, [mother]."
    pov "{i}Wow, she's really starting to like it. She didn't complain and the answer came so fast.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 059cb
    else:
        scene basement 10pm 059ca
    pov "{i}Oh my god. I can't wait.{/i}"
    mom "Don't try anything."
    pov "No, you choose what you want to do."
    pov "{i}Is she liking the idea that she's forced into special circumstances{/i}?"
    pov "{i}And so she has to do these things and she could still talk herself out of it.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 060cb
    else:
        scene basement 10pm 060ca
    pov "Wow..."
    if inc == True:
        pov "A good start, mom."
    else:
        pov "A good start, [mother]."
    mom "Hnn..."
    pov "{i}Her boobs are so damn fine and I can even see her panties.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 061cb
    else:
        scene basement 10pm 061ca
    pov "That outfit stretches so much, maybe you should free your boobs."
    mom "Hnng..."
    if inc == True:
        pov "I'm trying to give you a good time too, mom. Don't be so unapproachable."
    else:
        pov "I'm trying to give you a good time too, [mother]. Don't be so unapproachable."
    pov "This sort of fun isn't so bad, don't you think so too?"
    mom "Hmm..."
    pov "{i}She's still confused, but I have a good feeling about this.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 062cb
    else:
        scene basement 10pm 062ca
    mom "Hnn..."
    pov "{i}Wow that's sexy. She's heating up.{/i}"
    pov "Amazing, just amazing."
    if base10pmnicred == True:
        scene basement 10pm 063cb
    else:
        scene basement 10pm 063ca
    pov "Now I really feel like a V.I.P."
    if inc == True:
        pov "That's our special relationship now, mom."
    else:
        pov "That's our special relationship now, [mother]."
    mom "Thank you [pov]."
    pov "{i}Good, no more stuttering. She's getting in heat. Now we can have much more fun.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 064cb
    else:
        scene basement 10pm 064ca
    pov "{i}That lewd view.{/i}"
    if inc == True:
        pov "I'm so proud of you, mom."
    else:
        pov "I'm so proud of you, [mother]."
    pov "That was really a good idea."
    mom "You really like it [pov]?"
    pov "You have no idea!"
    pov "{i}But it's time to show her how much I like it.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 065cb
    else:
        scene basement 10pm 065ca
    mom "What are you doing?"
    pov "I'll show you how much I like your dancing."
    mom "But you... you..."
    "You release your dick."
    if base10pmnicred == True:
        scene basement 10pm 066cb
    else:
        scene basement 10pm 066ca
    pov "See? I like your dancing very much."
    mom "You... released your... penis..."
    pov "Yes and the way you look at it tells me that you like my appreciation for you."
    mom "It's... not... <stare>"
    if base10pmnicred == True:
        scene basement 10pm 067cb
    else:
        scene basement 10pm 067ca
    if inc == True:
        pov "So how about a deal, mom?"
    else:
        pov "So how about a deal, [mother]?"
    pov "I know you want to taste it, but you won't admit it."
    pov "So I can give you something in return."
    mom "..."
    pov "You don't want to be everybody's darling in the gang and Bruce won't stand up for you."
    pov "He's a loser, you know that."
    pov "Davide won't help you either, so you have no chance to get into a better position."
    if base10pmnicred == True:
        scene basement 10pm 068cb
    else:
        scene basement 10pm 068ca
    pov "Unless you help me and yourself."
    pov "I can talk Davide into something."
    pov "{i}Oh she's thinking...{/i}"
    pov "And it would be our secret of course. No one else would ever knew."
    mom "Hnn..."
    if base10pmnicred == True:
        scene basement 10pm 069cbbj
    else:
        scene basement 10pm 069cabj
    pov "Very good, so we've a deal."
    mom "Please don't tell anyone."
    pov "Yes, as I said. it'll be our dirty little secret."
    pov "{i}Damn, I can't believe I talked her into this.{/i}"
    if inc == True:
        pov "{i}My own mom is pleasuring me.{/i}."
    else:
        pov "{i}My mom's best friend is pleasuring me.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 070cbbj
    else:
        scene basement 10pm 070cabj
    pov "{i}That lewd staring.{/i}"
    if inc == True:
        pov "This is so good mom."
    else:
        pov "This is so good [mother]."
    mom "<lick>"
    pov "You're tongue is amazing."
    mom "Don't forget our deal."
    pov "How could I ever forget that?"
    if base10pmnicred == True:
        scene basement 10pm 071cbbj
    else:
        scene basement 10pm 071cabj
    pov "Oh yes!"
    mom "<suck>"
    pov "Take it in your mouth! Give me a good blowjob."
    mom "Hm... <suck>"
    if base10pmnicred == True:
        scene basement 10pm 072cbbj
    else:
        scene basement 10pm 072cabj
    pov "Ohh..."
    if inc == True:
        pov "You're so good to me, mom!"
    else:
        pov "You're so good to me, [mother]!"
    mom "<suck> <lick>"
    pov "{i}Amazing! But should I help her?{/i}"
    call screen base10nicbjchoose

screen base10nicbjchoose():
    default tt = Tooltip (" ")

    fixed:

        imagebutton auto "gui/icons/icon_corruption_%s.png" xpos 605 ypos 62 action (Hide ('base10nicbjchoose'), Jump('base10pmnicdp')) hovered tt.Action ("Help her (deepthroat) [cr1]") focus_mask True
        imagebutton auto "gui/icons/icon_abort_%s.png" xpos 605 ypos 225 action (Hide ('base10nicbjchoose'), Jump('base10pmnicbj')) hovered tt.Action ("Let her be") focus_mask True

    frame:
        xalign .5
        text tt.value

label base10pmnicdp:
    pov "Let me help you!"
    if base10pmnicred == True:
        scene basement 10pm 072cbbjdp
    else:
        scene basement 10pm 072cabjdp
    mom "Hnng?"
    if inc == True:
        pov "Be a good mom and let me help you."
    else:
        pov "Be a good girl and let me help you."
    pov "You need to satisfy me to complete the deal."
    if base10pmnicred == True:
        image dtred_basement = Movie(channel="dtred_basement", play="images/anim/dtred_basement.webm")
        scene dtred_basement with dissolve:
            size (config.screen_width, config.screen_height)
        pause
    else:
        image dt_basement = Movie(channel="dt_basement", play="images/anim/dt_basement.webm")
        scene dt_basement with dissolve:
            size (config.screen_width, config.screen_height)
        pause
    pov "Good! Take me deep."
    mom "Hmm... <suck>"
    if inc == True:
        pov "I'm in heaven. My mom is deepthroating me!"
        pov "You make me very happy, mom."
        pov "Fulfilling your son's wish."
    else:
        pov "I'm in heaven. [mother] is deepthroating me!"
        pov "You make me very happy, [mother]."
        pov "Fulfilling my wish."
    pov "{i}Oh yes, she can take it even deeper.{/i}"
    mom "<suck> <choke>"
    pov "That is so hot. Endure it just a little bit longer. I'll cum very soon."
    if base10pmnicred == True:
        scene basement 10pm 074cbbjdp
    else:
        scene basement 10pm 074cabjdp
    if inc == True:
        pov "{i}Deep in my mom's throat!{/i}"
        pov "Oh yes, HNG!"
        pov "I'm cumming! I'm cumming in your throat, mom!"
    else:
        pov "{i}Deep in [mother]'s throat!{/i}"
        pov "Oh yes, HNG!"
        pov "I'm cumming! I'm cumming in your throat, [mother]!"
    mom "HNNG! <gulp> <gulp>"
    pov "Yes good. Swallow it all!"
    if base10pmnicred == True:
        scene basement 10pm 075cbbjdp
    else:
        scene basement 10pm 075cabjdp
    mom "Are you crazy? Forcing me like this?"
    pov "Don't play innocent! As I pressed you down, you didn't struggle."
    mom "Maybe, maybe not. But you forced me to swallow."
    pov "Yes, as a part of our dirty secret."
    if inc == True:
        pov "You had to work to fulfill our deal, mom."
    else:
        pov "You had to work to fulfill our deal, [mother]."
    mom "Hnn..."
    mom "You better make your part, [pov]."
    pov "Yes, don't worry."
    pov "{i}Or do I need more help, haha?{/i}"
    jump base10pmniccorend

label base10pmnicbj:
    pov "{i}Let's see what she's up to.{/i}"
    if base10pmnicred == True:
        scene basement 10pm 073cbbj
    else:
        scene basement 10pm 073cabj
    if inc == True:
        pov "Oh yes mom! Pleasure me more!"
    else:
        pov "Oh yes [mother]! Pleasure me more!"
    mom "Hmm... <suck>"
    pov "You enjoy this too, don't you?"
    mom "Hmm... yesh..."
    pov "Then I'm happy, that we can share this dirty secret."
    "She sucks you wilder."
    pov "Oh, oh."
    if inc == True:
        pov "I'm about to cum, mom!"
    else:
        pov "I'm about to cum, [mother]!"
    call screen base10pmnicbjcum

screen base10pmnicbjcum():
    default tt = Tooltip (" ")

    fixed:

        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 605 ypos 62 action (Hide ('base10pmnicbjcum'), Jump('base10pmnicbjm')) hovered tt.Action ("Cum in her mouth") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 605 ypos 225 action (Hide ('base10pmnicbjcum'), Jump('base10pmnicbjf')) hovered tt.Action ("Cum on her face") focus_mask True

    frame:
        xalign .5
        text tt.value

label base10pmnicbjf:
    if inc == True:
        pov "I need to mark you, mom!"
    else:
        pov "I need to mark you, [mother]!"
    mom "Hm..."
    if base10pmnicred == True:
        scene basement 10pm 074cbbjf
    else:
        scene basement 10pm 074cabjf
    pov "HNG! Oh yes!"
    "You cum on her face."
    if base10pmnicred == True:
        scene basement 10pm 075cbbjf
    else:
        scene basement 10pm 075cabjf
    pov "Wow!"
    mom "You came a lot."
    if inc == True:
        pov "You gave me a blowjob, mom!"
    else:
        pov "You gave me a blowjob, [mother]!"
    pov "I gave my best and could repeat it anytime."
    mom "I can feel it... on my face."
    pov "What you can do with your mouth is just amazing."
    mom "Maybe... but don't forget me."
    pov "Yes, a deal is a deal."
    pov "{i}But maybe I could need some more help, haha?{/i}"
    jump base10pmniccorend

label base10pmnicbjm:
    if inc == True:
        pov "I need to cum in your mouth, mom!"
    else:
        pov "I need to cum in your mouth, [mother]!"
    mom "Hm..."
    pov "HNG! Oh yes!"
    "You cum in her mouth."
    if base10pmnicred == True:
        scene basement 10pm 074cbbjm
    else:
        scene basement 10pm 074cabjm
    pov "{i}Oh god. She shows me my cum.{/i}"
    pov "You see how good you pleasured me? I sure came a lot."
    mom "Hnng..."
    if inc == True:
        pov "Now be a good mom and swallow my sperm."
        pov "Taste your son's potent seed."
    else:
        pov "Now be a good girl and swallow my sperm."
        pov "Taste my potent seed."
    if base10pmnicred == True:
        scene basement 10pm 075cbbjm
    else:
        scene basement 10pm 075cabjm
    mom "<gulp> <gulp>"
    pov "{i}It's even so much that she can't swallow it at once.{/i}"
    pov "{i}And that lewd stare she give me. She liked it too, I'm sure.{/i}"
    mom "<gulp>"
    if base10pmnicred == True:
        scene basement 10pm 076cbbjm
    else:
        scene basement 10pm 076cabjm
    pov "{i}She even opens her mouth to prove me that she swallowed all.{/i}"
    if inc == True:
        pov "Very good mom. I'm so glad you could taste me."
    else:
        pov "Very good [mother]. I'm so glad you could taste me."
    mom "I did that just for you."
    pov "And I appreciate that very much."
    mom "You came a lot."
    if inc == True:
        pov "You gave me a blowjob, mom!"
    else:
        pov "You gave me a blowjob, [mother]!"
    pov "I gave my best and could repeat it anytime."
    mom "I had to swallow many times."
    pov "What you can do with your mouth is just amazing."
    mom "Maybe... but don't forget me."
    pov "Yes, a deal is a deal."
    pov "{i}But maybe I could need some more help, haha?{/i}"
    jump base10pmniccorend

label base10pmniccorend:
    scene black
    "Satisfied you leave the basement."
    $ base10pmnicred = False
    $ dtime += 1
    $ mombasementfirst = True
    jump kitchen


label base10pmnicntr:
    if gamemusic == True:
        stop music fadeout 2
        play music "music/NTR.mp3"
    $ basement10pmnicolentrfirst = True
    scene livingroom 10pm 010c
    dad "But first we had to carry the bags away."
    pov "And then we join them?"
    dad "Yes."
    scene livingroom 10pm 011c
    pov "{i}So let's do this then.{/i}"
    scene black
    "You carry the bags with Bruce away."
    dad "Now it's time to enter the basement."
    scene basement 10pm 012c
    mom "Hahaha, you're kidding me!"
    davide "No, I'm serious."
    if inc == True:
        dad "Your mother already drank a little to much again."
    else:
        dad "She already drank a little to much again."
    if momdrugfirst == True:
        pov "{i}At least he didn't drug her.{/i}"
    else:
        pov "{i}I wonder if he drugged her too{/i}."
    dad "You have to stay strong to endure this [pov]."
    pov "What?"
    pov "{i}What's he talking about?{/i}"
    scene basement 10pm 013c
    mom "I'll go change."
    davide "Yes, but don't let us wait!"
    davide "So it's your first time down there with the gang."
    pov "Yes..."
    davide "You'll like it, maybe not today, but soon..."
    pov "What do you mean?"
    scene basement 10pm 014c
    davide "Let's sit together so we can talk more."
    pov "OK."
    scene basement 10pm 016c
    davide "Normally we have the greatest parties in here, with much of women and other fun, haha."
    pov "Other fun?"
    dad "He mean the sex drugs."
    davide "Shut up Bruce! I'm talking now!"
    dad "Sorry, boss."
    pov "What you mean with normally?"
    davide "The girls are on our other party location, you'll see it soon too."
    davide "For this time I'll introduce you to the gang rules for the parties."
    davide "You need to choose a chick for yourself soon, but you'll also stay free to taste others."
    davide "With the exception of my girl. You only allowed to have fun with her with my permission."
    dad "Which he gave almost never."
    scene basement 10pm 015c
    davide "I said shut the fuck up!"
    dad "..."
    pov "{i}Why is he enduring this?{/i}"
    if inc == True:
        pov "So whom have you chosen, dad?"
    else:
        pov "So whom have you chosen, Bruce?"
    davide "Oh he isn't allow to choose. He has the lowest rank so he's allowed to watch only."
    davide "And you love to watch, don't you? Loser, haha!"
    dad "..."
    pov "{i}So he's really that kind of loser? Just watching and never stand up against Davide?{/i}"
    pov "And which girl have you chosen, Davide?"
    scene basement 10pm 017c
    davide "Oh there she is! You really take your time, girl!"
    mom "Yes, I needed a moment."
    davide "How about you bring us some drinks now, we have to celebrate our newest gang member."
    mom "Sure, Davide."
    scene basement 10pm 018c
    mom "Here, take a glass."
    if inc == True:
        pov "Thank you, mom."
    else:
        pov "Thank you, [mother]."
    pov "And you wearing a hot outfit."
    mom "Yes, it was someone's wish."
    scene basement 10pm 019c
    mom "Here's a drink for you too."
    davide "Good I need one."
    pov "{i}Holy shit. She don't wear panties with that outfit.{/i}"
    pov "{i}And it's very lewd with that open backside.{/i}"
    davide "Now come here, I need more service!"
    mom "Yes Davide. Let me just take the tablet down."
    scene basement 10pm 020c
    davide "Haha, don't look so sad loser! Your slutty wife couldn't resist any longer."
    call screen base10pmnicntrchoose

screen base10pmnicntrchoose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_approve_%s.png" xpos 644 ypos 251 action (Hide ('base10pmnicntrchoose'), Jump('base10pmnicntrlike')) hovered tt.Action ("Like NTR") focus_mask True
        imagebutton auto "gui/icons/icon_disapprove_%s.png" xpos 1026 ypos 251 action (Hide ('base10pmnicntrchoose'), Jump('base10pmnicntrhate')) hovered tt.Action ("Hate NTR") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmnicntrlike:
    $ base10pmlikentr = True
    jump base10pmnicntrhate

label base10pmnicntrhate:
    if base10pmlikentr == True:
        pov "{i}He's letting Davide humiliate him. He's really a loser.{/i}"
    else:
        pov "{i}Why aren't he stand up? Stop being such a loser!{/i}"
    mom "<lick> <lick>"
    davide "She's really craving for my big dick!"
    dad "..."
    davide "So you like what I'm doing with your wife?"
    dad "..."
    scene basement 10pm 021c
    if inc == True:
        davide "You like how your slutty mother working on my dick?"
    else:
        davide "You like how the slutty [mother] working on my dick?"
    pov "What?"
    davide "She's my slut, you won't find a better one!"
    if base10pmlikentr == False:
        pov "{i}Fuck you, you fucking prick!{/i}"
    if momdrugfirst == True:
        pov "{i}She does this only because you drugged her!{/i}"
    else:
        pov "{i}And she does it herself even without being drugged!{/i}"
    if base10pmlikentr == True:
        pov "{i}She's really a slut.{/i}"
    if inc == True:
        pov "{i}And dad is just sitting here and is trying to get drunk.{/i}"
    else:
        pov "{i}And Bruce is just sitting here and is trying to get drunk.{/i}"
    scene basement 10pm 022c
    davide "So time for more slut!"
    mom "Huh?"
    davide "What's wrong? I need your slutty pussy now!"
    mom "But you promised me that I would blow you only."
    davide "I don't care what I promised. I need to fuck you now!"
    if inc == True:
        mom "But not here with my son watching."
    else:
        mom "But not here with [pov] watching."
    if momdrugfirst == False:
        pov "{i}I wonder why she always won't let me watch? She shouldn't care about that when she's drugged, shouldn't she?{/i}"
    else:
        pov "{i}And she won't let me watch that I can't see how much she's loving it to be his slut. She has no more excuses without the drug.{/i}"
    scene basement 10pm 023c
    davide "Are you kidding me? Come here now, slut!"
    mom "Please, Davide. I'll make it up to you!"
    davide "No! My dick needs a slutty pussy now!"
    scene basement 10pm 024c
    mom "No this isn't fair, stop it."
    davide "Is the already wet slut talking!"
    mom "It's just..."
    if base10pmlikentr == False:
        pov "{i}Just let her alone, asshole!{/i}"
    else:
        pov "{i}She's struggling, so she needs a rough ride.{/i}"
    scene basement 10pm 025c
    mom "Hah, you're to rough!"
    davide "What you're talking about, slut? You always like it that way!"
    if inc == True:
        davide "Or you just acting because your son is watching?"
    else:
        davide "Or you just acting because [pov] is watching?"
    mom "No..."
    davide "Stop bitching around! And now I want you to tell your loser husband how my dick is working in you!"
    mom "What?"
    davide "You heard me!"
    "Davide fucks her more rough."
    scene basement 10pm 026c
    mom "Hah, hah, wait..."
    davide "Your slutty wife is all wet!"
    mom "I'm... so sorry Bruce..."
    davide "Stop lying! Your pussy is clinging on my dick!"
    mom "Hah... Ahh..."
    if inc == True:
        davide "You're a bad wife and mom. Enjoying getting fucked in front of them!"
    else:
        davide "You're a bad wife. Enjoying getting fucked in front of your husband and the son of your best friend!"
    mom "No... Hah... ahh..."
    davide "So you need more?"
    scene basement 10pm 027c
    mom "HAH! Are you crazy? You'll tear me apart!"
    davide "I'll only fuck you harder today until you admit it to them!"
    mom "You can't be... hah... serious."
    dad "Argh!"
    if inc == True:
        pov "{i}Is dad crying?{/i}"
    else:
        pov "{i}Is Bruce crying?{/i}"
    davide "Yes I need to go deeper!"
    mom "Aahhh, hah stop. I can't hold your weight too."
    scene basement 10pm 028c
    mom "AAAHHH... HNNN..."
    davide "Hah she's cumming. Your bitch wife is cumming from my hard dick!"
    mom "Hnng... your big dick... so deep..."
    davide "So I need to reward her and release my spunk in her slutty pussy!"
    mom "Hnng... Hng..."
    scene basement 10pm 029c
    davide "Damn, that was a good rough fuck!"
    davide "And my spunk is already flooding out of her pussy."
    mom "Hnng..."
    davide "You liked it what I done with her, haha!"
    davide "Stop whining around, loser!"
    davide "Even [pov] just sitting there and stares."
    pov "..."
    scene basement 10pm 030c
    davide "We'll find you a dirty whore you can fuck, haha."
    davide "Your wife is mine!"
    mom "Hnng..."
    "Still shocked you walk over to her."
    scene basement 10pm 031c
    mom "Please forgive me... [pov]."
    if base10pmlikentr == True:
        pov "Don't worry, I liked it."
    else:
        pov "It wasn't your fault. He's just a prick."
    mom "Hnng... I'm so done..."
    scene black
    "Confused you leave her."
    $ dtime += 1
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump kitchen


label base10pmniclove:
    scene basement 10pm 048c
    mom "Hmm..."
    pov "Is something wrong?"
    mom "No, I'm just thinking..."
    pov "{i}What is she up to?{/i}"
    mom "Wait here, I want to show you something."
    pov "Oh, Ok."
    pov "{i}I hope I didn't do something wrong?{/i}"
    scene basement 10pm 050c
    mom "Hm... where is it?"
    pov "{i}She's going in the changing room? Wait she wants to show me?{/i}"
    mom "Just wait a moment [pov]."
    pov "Yeah, sure."
    pov "{i}I hope it's something good.{/i}"
    if angelfirst == True:
        jump base10pmnicbachoose
    elif momlove >= 80 and bunnyfirst == True and angelfirst == False:
        jump base10pmniclove3
    else:
        jump base10pmniclovebunny

label base10pmnicbachoose:
    call screen bunnyangel

screen bunnyangel():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_angel_%s.png" xpos 597 ypos 100 action (Hide ('bunnyangel'), Jump('base10pmniclove3')) hovered tt.Action ("Angel") focus_mask True
        imagebutton auto "gui/icons/icon_bunny_%s.png" xpos 1297 ypos 100 action (Hide ('bunnyangel'), Jump('base10pmniclovebunny')) hovered tt.Action ("Bunny") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmniclovebunny:
    scene basement 10pm 051la
    mom "Hey [pov]!"
    pov "Oh my god."
    mom "So you like it?"
    pov "Why... why..."
    mom "It's one of my favorite outfits and I wanted you to see it."
    pov "This is... wow."
    scene basement 10pm 052la
    mom "So you like the bunny?"
    pov "Oh yes, you're a very hot bunny."
    mom "<giggle> I knew you'd like it."
    pov "The hottest Playboy bunny ever."
    mom "Oh stop flattering. But nice boys deserve more."
    scene basement 10pm 053la
    mom "Here. So you can adore me more. <giggle>"
    pov "Wow! And even a cute bunny tail."
    pov "{i}What she's doing? Is she flirting with me?{/i}"
    pov "You're really an adorable bunny. But why did you choose that?"
    scene basement 10pm 054la
    mom "I wanted to be a real playboy bunny in the past."
    mom "And with this outfit I can be one and gain all the compliments."
    if inc == True:
        pov "Oh mom. You would be the hottest playboy bunny."
    else:
        pov "Oh [mother]. You would be the hottest playboy bunny."
    pov "I bet the old man would come back from his grave to have you in his house."
    mom "Haha, you know exactly how to charm me."
    mom "And that's why you get a treat now."
    scene basement 10pm 055la
    pov "{i}Wow. Is she going to kiss me now? Must... behave...{/i}"
    if inc == True:
        mom "I'm getting more and more proud of you, my son."
    else:
        mom "I'm getting more and more proud of you, [pov]."
    mom "You are so much like your father."
    pov "But I'm not him."
    pov "{i}She needs to stop comparing me with him.{/i}"
    mom "No, you aren't. You're much better."
    pov "{i}What? Wow.{/i}"
    scene basement 10pm 056la
    mom "<kiss> I love you [pov]!"
    pov "{i}Oh she's so romantic now. Kissing me on the cheek.{/i}"
    if inc == True:
        pov "I love you too, mom!"
    else:
        pov "I love you too, [mother]!"
    mom "I feel so free with you. Just the two of us."
    if inc == True:
        pov "I feel the same, mom."
    else:
        pov "I feel the same [mother]."
    scene basement 10pm 057la
    mom "If you can keep it a secret I'll tell you what bunnies really love."
    pov "Yes... I can keep any secret you want me to."
    pov "{i}The way she's looking at me. I need to know!{/i}"
    mom "Carrots!"
    pov "Carrots?"
    mom "Yes, bunnies love carrots."
    scene basement 10pm 058la
    mom "And I'd love to see your carrot."
    if inc == True:
        pov "Oh mom."
    else:
        pov "Oh [mother]."
    mom "Be a good boy and give this bunny your carrot."
    pov "I'll give you anything you want."
    pov "{i}Is this a dream?{/i}"
    scene basement 10pm 059la
    mom "Then follow me!"
    mom "Follow the bunny, [pov]."
    pov "Of course."
    pov "{i}Is she really playing with my carrot now. My dick! Damn, now I'm really confused.{/i}"
    mom "Just sit here and enjoy what a bunny can do."
    pov "Hm..."
    scene basement 10pm 060la
    mom "Just relax and enjoy what this bunny wants to do with your carrot."
    pov "Oh, I'll wait and enjoy!"
    mom "And promise that it'll be our secret."
    pov "I promise! And I would love to share even more secrets with you."
    mom "Without knowing what I'm going to do with you? You're so sweet."
    pov "It isn't anything bad, is it?"
    mom "You could get addicted <giggle>"
    scene basement 10pm 061la
    pov "Then I'll fall."
    mom "Time to see your carrot."
    "She's unpacking your dick."
    pov "{i}What a hot view. And that cleavage.{/i}"
    if inc == True:
        pov "{i}And the fact that my mom wants to play with my dick.{/i}"
    else:
        pov "{i}And the fact that [mother] wants to play with my dick.{/i}"
    scene basement 10pm 062la
    mom "<kiss>"
    pov "Oh yes. Kiss my carrot."
    mom "I need to taste it before <giggle>"
    pov "Before, is there more?"
    scene basement 10pm 063la
    mom "Before I eat my carrot, <giggle>"
    mom "<lick> <lick>"
    pov "{i}Is she really up to giving me a blowjob?{/i}"
    pov "{i}She's even playing with my balls. This is so great.{/i}"
    pov "I'm glad you like my carrot."
    mom "Yes, <lick> it tastes good."
    scene basement 10pm 064la
    mom "Hmm... <suck>"
    pov "Good, eat my carrot."
    if inc == True:
        pov "{i}Hell yeah. My mom is playing a naughty role-play with me and sucking me off.{/i}"
    else:
        pov "{i}Hell yeah. [mother] is playing a naughty role-play with me and sucking me off.{/i}"
    "Suddenly you feel her teeth on your dick."
    pov "HUH?"
    scene basement 10pm 065la
    mom "Haha... you're scared, aren't you?"
    pov "Haha, you got me there."
    if inc == True:
        mom "I would never hurt my baby boy."
    else:
        mom "I would never hurt you, [pov]."
    pov "Yeah, I trust you."
    mom "No worries, it was a little mean. But you can enjoy your reward more."
    pov "My reward?"
    mom "This rabbit wants some milk too. Not only a tasty carrot."
    pov "Oh my..."
    pov "{i}She wants to drink my sperm.{/i}"
    pov "That's really a good reward."
    scene basement 10pm 066la
    mom "Hm... <suck>"
    pov "Hah, you're doing so good."
    pov "{i}Is she pressing my dick in her cheek? That's so hot.{/i}"
    "Your penis is twitching like crazy."
    if inc == True:
        pov "Mom, I don't think I can't hold it any longer. Your pleasure is too much."
    else:
        pov "[mother], I don't think I can't hold it any longer. Your pleasure is too much."
    scene basement 10pm 067la
    mom "Not yet [pov]. Hold it a little longer. You'll love the release more!"
    "She squeezes your balls."
    pov "OK... I can do it."
    if inc == True:
        pov "{i}My mom is giving me sex-tips while sucking me!{/i}"
    else:
        pov "{i}[mother] is giving me sex-tips while sucking me!{/i}"
    pov "{i}And how she's playing with my balls. This is heaven.{/i}"
    mom "Now be a good boy and give me your milk."
    scene basement 10pm 068la
    "She stops the pressure on your balls."
    pov "HNG! Oh yes!"
    "You spurt your sperm in her mouth."
    pov "{i}I'm cumming in her mouth!{/i}"
    mom "Hnn... hm..."
    scene basement 10pm 069la
    mom "Your milk is tasty."
    pov "Oh!"
    mom "I'll drink your milk now!"
    if inc == True:
        pov "I'm so glad I could give it to you, mom!"
    else:
        pov "I'm so glad I could give it to you, [mother]!"
    scene basement 10pm 070la
    mom "Hmm... <gulp>"
    pov "{i}She's swallowing it.{/i}"
    if inc == True:
        pov "{i}My mom swallowed my sperm.{/i}"
    else:
        pov "{i}[mother] swallowed my sperm.{/i}"
    scene basement 10pm 072la
    mom "[pov]! You aren't confused now that I somewhat attacked you?"
    pov "Oh come on. Don't worry. I liked it very much!"
    pov "And I'd love to do more things with the bunny, haha."
    mom "Hmm..."
    if inc == True:
        pov "Come here, mom!"
    else:
        pov "Come here, [mother]!"
    scene basement 10pm 073la
    pov "Stop thinking bad thoughts."
    pov "I love you!"
    if inc == True:
        pov "And I love you even more than a normal son would love his mom."
        pov "In my dreams I want you to be my lover."
    else:
        pov "And I love you even more than I should."
        pov "In my dreams I want you to be my lover."
    mom "Oh [pov]. I love you so much!"
    "You hold her for a while."
    mom "Let's leave. I want to enjoy that moment in my thoughts."
    mom "And have sweet dreams of me."
    if inc == True:
        pov "Oh yes I will. Mom."
    else:
        pov "Oh yes I will. [mother]."
    scene black
    "You leave the basement."
    $ bunnyfirst = True
    $ dtime += 1
    jump kitchen

label base10pmniclove3:
    scene basement 10pm 051lb
    mom "So...?"
    pov "..."
    mom "Ha, can't find any words?"
    pov "You, you look like an angel."
    mom "Like an angel?"
    pov "Like a lingerie model!"
    scene basement 10pm 052lb
    mom "Oh, that's so sweet."
    pov "Thi... is... so... hot. Why are you... wearing this?"
    mom "It's my present for you being such a gentleman. You're the first one to see it."
    pov "That's a good present."
    mom "Oh it gets even better."
    scene basement 10pm 053lb
    pov "Ohh... <gulp>"
    mom "<giggle> So you like it?"
    pov "That string is making your ass so hot!"
    mom "Hm..."
    pov "Oh, sorry. I won't say it like that."
    scene basement 10pm 054lb
    mom "Haha, calm down [pov]."
    mom "That sort of lingerie is intended to make men confused, <giggle>."
    mom "But it makes me happy that you still try to be a gentleman."
    pov "It's very hard right now."
    scene basement 10pm 055lb
    mom "Finding words or something else? <giggle>"
    if inc == True:
        pov "What are you doing with me, mom?"
    else:
        pov "What are you doing with me, [mother]?"
    mom "I'm not that stupid. I noticed a young gentleman giving me special attention."
    if inc == True:
        pov "I... just love you, mom!"
    else:
        pov "I... just love you, [mother]!"
    mom "I know, but your staring tells me that you're loving something else much more."
    pov "I... can't... sorry."
    scene basement 10pm 056lb
    mom "Now you should see better!"
    pov "Oh my god! They're so beautiful!"
    pov "But why... why I'm getting all this?"
    mom "I'm just so proud of you, you became such a good young man, but I noticed you're also confused around me."
    mom "Let's have a special basement time together and let's forget everything else."
    mom "I see now only a good looking young man that adores me."
    scene basement 10pm 057lb
    pov "And I see the hottest woman on earth!"
    mom "Than take your chance."
    pov "My chance?"
    mom "You want to touch them?"
    scene basement 10pm 058lbb
    pov "They're so big and firm, but still soft like pillows."
    mom "Just never stop complimenting me."
    pov "These would be two good reasons to stay on the good path."
    pov "I wish I could remember sucking milk out of them as a baby."
    mom "Hm..."
    pov "And I wish even more to suck some milk out of them again."
    scene basement 10pm 059lbb
    mom "But then I need to get pregnant."
    pov "..."
    mom "..."
    pov "..."
    mom "Time for your reward!"
    pov "My... reward..."
    mom "Go over to the table."
    scene basement 10pm 060lb
    mom "It'll be something just for you."
    if inc == True:
        pov "Oh mom. I'm so happy right now and it gets even better?"
    else:
        pov "Oh [mother]. I'm so happy right now and it gets even better?"
    mom "Relax and try to endure so I can't enjoy it also."
    pov "I... will..."
    scene basement 10pm 061lb
    mom "But first we need to prepare you."
    "She unpacks your dick."
    pov "{i}And I'm already so hard right now.{/i}"
    scene basement 10pm 062lb
    mom "<kiss>"
    if inc == True:
        pov "Oh mom."
    else:
        pov "Oh [mother]."
    mom "You're twitching in anticipation already, try to relax, [pov]."
    pov "It's so hard when you're touch me there with your lips."
    scene basement 10pm 063lb
    mom "We need to make it wet before."
    pov "Oh my balls."
    "She squeezes your balls."
    mom "Feels good, doesn't it?"
    pov "Oh yes..."
    mom "I know you want to try something else maybe, so you can choose yourself."
    pov "Choose?"
    mom "Do you want me to continue with my mouth or do you want to feel my breasts?"
    pov "{i}Hell yes! But her mouth is also so soft.{/i}"
    call screen base10pmniclove3choose

screen base10pmniclove3choose():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1443 ypos 170 action (Hide ('base10pmniclove3choose'), Jump('base10pmniclove3bj')) hovered tt.Action ("Let her use her mouth") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1443 ypos 365 action (Hide ('base10pmniclove3choose'), Jump('base10pmniclove3boobs')) hovered tt.Action ("Let her use her boobs") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmniclove3bj:
    if inc == True:
        pov "Please continue with your mouth, mom."
        mom "As you wish, my lovely son."
    else:
        pov "Please continue with your mouth, [mother]."
        mom "As you wish, lovely [pov],"
    scene basement 10pm 064lb
    mom "<suck>"
    pov "Oh yes!"
    if inc == True:
        pov "{i}Hell yeah. My mom is rewarding me by sucking me off.{/i}"
    else:
        pov "{i}Hell yeah. [mother] is rewarding me by sucking me off.{/i}"
    pov "Your soft lips and that wet tongue. It's so hard to calm myself down."
    scene basement 10pm 065lb
    "She squeezes your balls harder."
    mom "<giggle> So I have to do this to help you endure a little longer."
    pov "Then... I'll cum so much."
    mom "That's a good way to make my reward unforgettable."
    if inc == True:
        pov "I'll be the best son forever, if I'll get such good rewards from you mom!"
    else:
        pov "I'll be the best man forever, if I'll get such good rewards from you [mother]!"
    mom "So nice!"
    scene basement 10pm 066lb
    mom "<suck> <lick>"
    pov "I must be in heaven, having an angel sucking on my dick."
    mom "Hm... hnn..."
    pov "I wish I could do this forever with you."
    mom "<giggle> <suck>"
    scene basement 10pm 067lb
    mom "You're such a charmer. Even when you're at the limit you show manners."
    pov "A dream is coming true. I'm just enjoying it as much as possible."
    mom "So you can enjoy it even more. I know you can't hold out any longer, even when I hold your balls."
    if inc == True:
        pov "Yes, I'm gonna cum so hard mom."
    else:
        pov "Yes, I'm gonna cum so hard [mother]."
    mom "You can choose where to spray it."
    pov "..."
    mom "<giggle>"
    call screen base10pmniclove3bjcum

screen base10pmniclove3bjcum():
    default tt = Tooltip (" ")

    fixed:
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 700 ypos 126 action (Hide ('base10pmniclove3bjcum'), Jump('base10pmniclove3bjmouth')) hovered tt.Action ("Cum in her mouth") focus_mask True
        imagebutton auto "gui/icons/icon_unihand_%s.png" xpos 1420 ypos 126 action (Hide ('base10pmniclove3bjcum'), Jump('base10pmniclove3bjface')) hovered tt.Action ("Cum on her face") focus_mask True


    frame:
        xalign .5
        text tt.value

label base10pmniclove3bjmouth:
    pov "I want you to taste my sperm."
    if inc == True:
        mom "As you wish, my son."
    else:
        mom "As you wish, [pov]."
    scene basement 10pm 068lb
    "She stops the pressure on your balls."
    pov "HNG! Oh yes!"
    "You spurt your sperm in her mouth."
    pov "{i}I'm cumming in her mouth!{/i}"
    mom "Hnn... hm..."
    scene basement 10pm 069lb
    mom "You came very much. So you liked my reward?"
    pov "I loved it!"
    mom "And you even taste not so bad."
    scene basement 10pm 070lb
    mom "Hmm... <gulp>"
    pov "{i}She's swallowing it.{/i}"
    if inc == True:
        pov "{i}My mom swallowed my sperm.{/i}"
    else:
        pov "{i}[mother] swallowed my sperm.{/i}"
    scene basement 10pm 072lb
    mom "Tasty!"
    pov "Now you're complimenting me."
    mom "<giggle>"
    jump base10pmniclove3end

label base10pmniclove3end:
    mom "Please make sure this will be our secret."
    pov "I'll rather cut my tongue then tell anyone."
    mom "Come here, my charmer."
    scene basement 10pm 073lb
    if inc == True:
        pov "I love you so much, mom!"
        mom "I love you too, my son!"
    else:
        pov "I love you so much, [mother]!"
        mom "I love you too, [pov]!"
    mom "And when my good boy behaves we can repeat this anytime."
    pov "Oh I'll be looking forward to that."
    "You hold her for a while."
    mom "Let's leave. I want to enjoy that moment in my thoughts."
    mom "And have sweet dreams of me."
    if inc == True:
        pov "Oh yes I will. Mom."
    else:
        pov "Oh yes I will. [mother]."
    scene black
    "You leave the basement."
    $ angelfirst = True
    $ dtime += 1
    jump kitchen

label base10pmniclove3bjface:
    pov "I want to paint your beautiful face."
    if inc == True:
        mom "As you wish, my son."
    else:
        mom "As you wish, [pov]."
    scene basement 10pm 068lbf
    "She stops the pressure on your balls."
    pov "HNG! Oh yes!"
    "You spray your sperm on her face."
    pov "{i}I'm cumming on her face!{/i}"
    mom "Hnn... hm..."
    scene basement 10pm 069lbf
    mom "You came very much. So you liked my reward?"
    pov "I loved it!"
    mom "It's so warm and sticky."
    pov "Even now you look so beautiful."
    mom "I would like to enjoy your scent more on me, but you came so much, <giggle>"
    pov "You can remove it anytime, that beautiful view is burned in my mind."
    mom "<giggle>"
    jump base10pmniclove3end

label base10pmniclove3boobs:
    if inc == True:
        pov "Please let me feel your boobs on my dick, mom."
        mom "As you wish, my lovely son."
    else:
        pov "Please let me feel your boobs on my dick, [mother]."
        mom "As you wish, lovely [pov],"
    scene basement 10pm 062lbbj
    pov "So... so soft..."
    mom "Your penis likes his new place."
    pov "He's meeting two new friends."
    mom "<giggle>"
    pov "And I hope they'll become friends for life."
    mom "Save your breath for later, you'll need it to relax, I feel your excitement already."
    scene basement 10pm 063lbbj
    mom "<kiss>"
    pov "The best view ever."
    if inc == True:
        pov "{i}Getting a boob job from my mom.{/i}"
    else:
        pov "{i}Getting a boob job from [mother]{/i}."
    scene basement 10pm 064lbbj
    mom "I see you enjoying this very much!"
    if inc == True:
        pov "Getting a boob job from my beautiful mom. It's the best thing ever!"
    else:
        pov "Getting a boob job from you. It's the best thing ever!"
    mom "And feeling your warm penis twitching between them is also nice."
    pov "Then I'm glad you can enjoy my reward too."
    mom "<giggle> Oh yes, I do."
    scene basement 10pm 065lbbj
    mom "How about some more playing?"
    pov "Ohh... ohh... this is so good!"
    mom "I'll squeeze them hard together, just try to press your sperm out and you'll enjoy a very good feeling."
    if inc == True:
        pov "I love you giving me tips on this, mom."
    else:
        pov "I love you giving me tips on this, [mother]."
    "She begins to squeeze her boobs together."
    scene basement 10pm 066lbbj
    pov "HNG!"
    mom "Good, press more."
    pov "Hah, ahh..."
    mom "Come for me, [pov]!"
    scene basement 10pm 067lbbj
    pov "Haaah..."
    mom "Good!"
    "You spray your sperm out."
    pov "This... hah... is so good!"
    mom "Give it to me."
    pov "Hnn... I love you!"
    scene basement 10pm 068lbbj
    mom "Good, you sure came a lot."
    if inc == True:
        pov "That was so wonderful, mom."
    else:
        pov "That was so wonderful, [mother]."
    mom "And so much from your warm, sticky sperm on me."
    pov "And it gives me such an amazing view too."
    mom "You won the hard fight, <giggle>"
    jump base10pmniclove3end


label basement23listen:
    hide screen locations
    if gamemusic == True:
        stop music fadeout 2
        play music "music/NTR.mp3"
    scene main basement door
    pov "{i}Maybe I can hear something?{/i}"
    dad "No wait! You shouldn't do that."
    mom "Calm down, honey!"
    davide "I'll do what I want!"
    pov "{i}Whats happening?{/i}"
    mom "Oh my god!"
    davide "Nice!"
    mom "Aaah... hah... hah..."
    pov "{i}No, I can't believe it. Are they really doing it?{/i}"
    if inc == True:
        pov "{i}And dad is watching?{/i}"
    else:
        pov "{i}And Bruce is watching?{/i}"
    pov "{i}I'll have to find a way to get in the basement.{/i}"
    $ dtime += 1
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump basement


label basement24listen:
    hide screen locations
    if gamemusic == True:
        stop music fadeout 2
        play music "music/NTR.mp3"
    scene main basement door
    mom "Hah... aahh... please don't stop!"
    pov "{i}I don't want to hear this anymore! But I can't leave.{/i}"
    pov "{i}So I can at least pay attention when something else happens.{/i}"
    mom "Harder!"
    pov "{i}But they won't do this all night, will they?{/i}"
    mom "Hmm..."
    davide "Move your ass more!"
    pov "{i}That damn asshole!{/i}"
    $ dtime += 1
    if gamemusic == True:
        stop music fadeout 2
        play music "music/default.mp3"
    jump basement


label sellingdrugs1:
    hide screen locations
    scene basement bruce sell1
    pov "{i}What's he doing here? He seems to be sad.{/i}"
    if inc == True:
        pov "Dad?"
    else:
        pov "Bruce?"
    scene basement bruce sell2
    dad "[pov]!"
    dad "I need your help!"
    pov "What's up? What can I do?"
    scene basement bruce sell3
    dad "I promised Davide to sell some drugs, but I need to meet with someone he can't know."
    pov "From the police?"
    dad "Something like that, yeah."
    pov "You selling drugs here in the basement at this time?"
    dad "Yes, the people behave when they're here."
    pov "With the others above knowing nothing?"
    dad "Yes, the people come from the outside way in here and we have never had any problems."
    pov "OK, as you say."
    scene basement bruce sell4
    dad "I know you're a higher member, so I can only ask you to do it."
    if inc == True:
        pov "No problem dad, I can do it."
    else:
        pov "No problem Bruce, I can do it."
    scene basement bruce sell5
    dad "Thank you so much [pov]."
    dad "And feel free to sell them when ever you want."
    pov "You mean that I should sell them at other times too."
    dad "Yes, that'll be a good training for you how the gang is going."
    dad "You can learn much."
    pov "O... OK. What's the price?"
    dad "20 Bucks."
    $ selldrugs = True
    scene black
    "He leaves the basement."
    jump sellingdrugs2

label sellingdrugs2:
    hide screen locations
    $ randomnum = renpy.random.randint(1,2)
    if randomnum == 1:
        scene basement selling drugs male
    elif randomnum == 2:
        scene basement selling drugs female


    if randomnum == 1:
        "Customer" "One candy please."
        pov "20 Bucks."
        "Customer" "Here."
        $ money += 20
    elif randomnum == 2:
        "Customer" "Two candies please."
        pov "40 Bucks."
        "Customer" "Hm..."
        $ money += 40





    $ selldrugsamount += 1
    scene black
    if selldrugsamount == 1:
        jump sellingdrugs2
    else:
        "No more customers for today."
    $ dtime += 1
    jump kitchen
# Decompiled by unrpyc: https://github.com/CensoredUsername/unrpyc
