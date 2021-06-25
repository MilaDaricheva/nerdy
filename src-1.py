// This source code is subject to the terms of the Mozilla Public License 2.0 at https: // mozilla.org/MPL/2.0/
// © auntmotya

//@version = 4
strategy("VP-Nerdy-Steps", overlay=true, pyramiding=5, initial_capital=50000, calc_on_every_tick=false, currency="USD", default_qty_value=1)
//new rules


///////////////////////////////////////////////////
// Last bars low maybe 60 is better
// hist_data.py
lowestLow = lowest(low, 40)

// Last bars high
highestHigh = highest(high, 40)

// last 24 hr low
lowestLowBig = lowest(low, 1440)

// last 24 hr high
highestHighBig = highest(high, 1440)

plotchar(lowestLowBig, "lowestLowBig", "", location.top)
plotchar(highestHighBig, "highestHighBig", "", location.top)

///////////////////////////////////////////////////
// Generate array of VP
// demo.py init

lenMainVP = 50
float[] mainVP = array.new_float(0)
sVP = 3880.51
step = 13.065

for i = 0 to lenMainVP-1
   array.push(mainVP, sVP)
    sVP := sVP+step

// rt_data.py
float aroundVPLevel = 0
for i = 0 to lenMainVP-1
   if low <= array.get(mainVP, i) + 3 and close > array.get(mainVP, i) and (high - low < 7) and lowestLow > array.get(mainVP, i) - 1
       aroundVPLevel := array.get(mainVP, i)

plotshape(aroundVPLevel > 0, style=shape.triangleup, location=location.belowbar, color=color.new(color.blue, 80), size=size.small)

float aroundVPLevelToShort = 0
for i = 0 to lenMainVP-1
   if high < array.get(mainVP, i) + 1 and high >= array.get(mainVP, i) - 3 and (high - low < 7) and highestHigh < array.get(mainVP, i) + 1
       aroundVPLevelToShort := array.get(mainVP, i)

plotshape(aroundVPLevelToShort > 0, style=shape.triangledown, location=location.abovebar, color=color.new(color.red, 80), size=size.small)

///////////////////////////////////////////////////
// Remember Levels
var float rememberVPlevel = aroundVPLevel
if rememberVPlevel[1] != aroundVPLevel and aroundVPLevel > 0
   rememberVPlevel := aroundVPLevel

//plotchar(rememberVPlevel, "rememberVPlevel", "", location.top)

var float rememberVPlevelShort = aroundVPLevelToShort
if rememberVPlevelShort[1] != aroundVPLevelToShort and aroundVPLevelToShort > 0
   rememberVPlevelShort := aroundVPLevelToShort

plotchar(rememberVPlevelShort, "rememberVPlevelShort", "", location.top)

///////////////////////////////////////////////////
// Time Management
timeinrange(res, sess) = > not na(time(res, sess)) ? 1: 0

whatstime = timeinrange("1", "1500-1705:123456")
//plotchar(whatstime, "whatstime", "", location.top)

closealltime = timeinrange("1", "1509-1511:123456")
//plotchar(closealltime, "closealltime", "", location.top)

cancelalltime = timeinrange("1", "1513-1515:123456")
//plotchar(cancelalltime, "cancelalltime", "", location.top)


///////////////////////////////////////////////////
// Steps
twoStepsFromHigh = highestHighBig - low > 1.8*step
twoStepsFromLow = high - lowestLowBig > 1.8*step

threeStepsFromHigh = highestHighBig - low > 2.8*step
threeStepsFromLow = high - lowestLowBig > 2.8*step

fourStepsFromHigh = highestHighBig - low > 3.7*step
fourStepsFromLow = high - lowestLowBig > 3.7*step

sixStepsFromHigh = highestHighBig - low > 5.7*step
sixStepsFromLow = high - lowestLowBig > 5.7*step


plotchar(twoStepsFromHigh, "twoStepsFromHigh", "", location.top)
plotchar(twoStepsFromLow, "twoStepsFromLow", "", location.top)
plotchar(threeStepsFromHigh, "threeStepsFromHigh", "", location.top)
plotchar(threeStepsFromLow, "threeStepsFromLow", "", location.top)
plotchar(fourStepsFromHigh, "fourStepsFromHigh", "", location.top)
plotchar(fourStepsFromLow, "fourStepsFromLow", "", location.top)
plotchar(sixStepsFromHigh, "sixStepsFromHigh", "", location.top)
plotchar(sixStepsFromLow, "sixStepsFromLow", "", location.top)

///////////////////////////////////////////////////
// EMA
// hist_data.py  strategy_management.py

ema30 = ema(close, 540)
emaUp = ema30 > ema30[60]
emaDown = ema30 < ema30[60]
emaDiff = ema30 - ema30[120]

emaD0 = emaDiff < 0.5 and emaDiff > -0.5
emaD1 = emaDiff < 1 and emaDiff > -1
emaD2 = emaDiff < 2 and emaDiff > -2
emaD3 = emaDiff < 3 and emaDiff > -3
emaD4 = emaDiff < 4 and emaDiff > -4
emaD5 = emaDiff < 5 and emaDiff > -5

lowestLowDiff = lowest(emaDiff, 1440)


plotchar(lowestLowDiff, "lowestLowDiff", "", location.top)
plotchar(emaDiff, "emaDiff", "", location.top)


///////////////////////////////////////////////////
// Entry & Exit signals

wobbleCond = twoStepsFromHigh and emaD1

trendCond = threeStepsFromHigh and emaD4 and not emaD1

strongCond = fourStepsFromHigh and not emaD4 and emaD5

extremeCond = sixStepsFromHigh and not emaD5

//order_management.py

flipLong = false
//Close shorts
if strategy.position_size < 0 and aroundVPLevel > 0
   cond1 = twoStepsFromHigh and emaUp
    cond2 = (wobbleCond or trendCond or strongCond or extremeCond) and emaDown
    cond3 = emaDiff > 0
    if cond1 or cond2 or cond3
       strategy.close_all(comment="Closed all Shorts", alert_message="Closed all Shorts")
        flipLong := true

canTrade = strategy.position_size == 0 and not whatstime

inLongTime = strategy.position_size > 0

timeInLongTrade = barssince(not inLongTime)

plotchar(timeInLongTrade, "timeInLongTrade", "", location.top)

//Start Long
if (canTrade and aroundVPLevel > 0) or flipLong[1]
   strategy.cancel("S1")
    strategy.cancel("S2")
    strategy.cancel("S3")

    if (twoStepsFromHigh and emaUp) or ((wobbleCond or trendCond or strongCond or extremeCond) and emaDown)
       if emaDiff < -2
            strategy.entry("L1", strategy.long, 1, limit=rememberVPlevel, alert_message="Started Long")
            if extremeCond
                strategy.entry("L2", strategy.long, 2, limit=rememberVPlevel - 13, alert_message="Added Long")
        else
            strategy.entry("L1", strategy.long, 1, alert_message = "Started Long")
            strategy.entry("L2", strategy.long, 2, limit = rememberVPlevel - 10, alert_message = "Added Long")
            strategy.entry("L3", strategy.long, 2, limit = rememberVPlevel - 20, alert_message = "Added Long")

target1 = 92
target2 = 92
target3 = 92

// Determine stop loss prices
longStopPrice = rememberVPlevel - 28

//if strategy.position_size == 0 and emaDiff < -2
// strategy.cancel("L2")
// strategy.cancel("L3")
// longStopPrice := strategy.position_avg_price - 10

if strategy.position_size > 0 and timeInLongTrade > 620
   strategy.cancel("L2")
    strategy.cancel("L3")
    longStopPrice := strategy.position_avg_price - 10

if strategy.position_size[1] == 3 and strategy.position_size == 1
   strategy.cancel("L2")
    strategy.cancel("L3")
    longStopPrice := strategy.position_avg_price + 10

if emaDiff > 1.5 and strategy.position_size == 1
   target1 := 200

if emaDiff > 4 and strategy.position_size == 1
   target1 := 400

//should never get bigger during the open trade
if longStopPrice < longStopPrice[1] and strategy.position_size > 0 and timeInLongTrade > 5
   longStopPrice := longStopPrice[1]

plotchar(longStopPrice, "longStopPrice", "", location.top)

strategy.exit("exit long", from_entry="L1", qty=1, profit= target1, stop = longStopPrice, alert_message = "Closed Long")
strategy.exit("exit long", from_entry="L2", qty=2, profit= target2, stop = longStopPrice, alert_message = "Closed Long")
strategy.exit("exit long", from_entry="L3", qty=2, profit= target3, stop = longStopPrice, alert_message = "Closed Long")

//demo.py
//cancel scales if position closed
if strategy.position_size[1] > 0 and strategy.position_size <= 0
   strategy.cancel("L2")
    strategy.cancel("L3")


///////////////////////////////////////////////////
// Short Entries

wobbleCondS = twoStepsFromLow and emaD1

trendCondS = threeStepsFromLow and emaD4 and not emaD1

strongCondS = fourStepsFromLow and not emaD4 and emaD5

extremeCondS = sixStepsFromLow and not emaD5

lastDump = barssince(sixStepsFromHigh)

if not lastDump
    if lastDump[1] > 0
        lastDump := lastDump[1] + 1
    else
        lastDump := 1441

plotchar(lastDump, "lastDump", "", location.top)


canShort = strategy.position_size == 0 and not whatstime

flipShort = false

inShortTime = strategy.position_size < 0

timeInShortTrade = barssince(not inShortTime)

plotchar(timeInShortTrade, "timeInShortTrade", "", location.top)

//order_management.py

//Close longs
if strategy.position_size > 0 and aroundVPLevelToShort > 0
   if (twoStepsFromLow and emaDown and lastDump > 1440) or ((wobbleCondS or trendCondS or strongCondS or extremeCondS) and emaUp and lastDump > 1440)
       strategy.close_all(comment = "Closed All Longs", alert_message = "Closed All Longs")
        flipShort := true


//Start Short
if (canShort and aroundVPLevelToShort > 0) or flipShort[1]
   strategy.cancel("L1")
    strategy.cancel("L2")
    strategy.cancel("L3")

    if (twoStepsFromLow and emaDown and lastDump > 1440) or ((wobbleCondS or trendCondS or strongCondS or extremeCondS) and emaUp and lastDump > 1440)
        if emaDiff > 2
            strategy.entry("S1", strategy.short, 1, limit = rememberVPlevelShort, alert_message = "Started Short")
        else
            strategy.entry("S1", strategy.short, 1, alert_message = "Started Short")
            strategy.entry("S2", strategy.short, 2, limit= rememberVPlevelShort + 10, alert_message = "Added Short")
            strategy.entry("S3", strategy.short, 2, limit= rememberVPlevelShort + 20, alert_message = "Added Short")

//Stop Price
shortStopPrice = rememberVPlevelShort + 28

targetS1 = 92
targetS2 = 92
targetS3 = 92

//if strategy.position_size == 0 and emaDiff > 2
// strategy.cancel("S2")
// strategy.cancel("S3")
// shortStopPrice := strategy.position_avg_price + 10

if strategy.position_size < 0 and timeInShortTrade > 620
   strategy.cancel("S2")
    strategy.cancel("S3")
    //targetS1 := 80
    shortStopPrice := strategy.position_avg_price + 10

if strategy.position_size[1] == -3 and strategy.position_size == -1
   strategy.cancel("S2")
    strategy.cancel("S3")
    shortStopPrice := strategy.position_avg_price - 10

if emaDiff < -1.5 and strategy.position_size == -1
   targetS1 := 200

if emaDiff < -4 and strategy.position_size == -1
   targetS1 := 400

//should never get bigger during the open trade
if shortStopPrice > shortStopPrice[1] and strategy.position_size < 0 and timeInShortTrade > 5
   shortStopPrice := shortStopPrice[1]

plotchar(shortStopPrice, "shortStopPrice", "", location.top)

strategy.exit("exit short", from_entry="S1", qty=1, profit= targetS1, stop = shortStopPrice, alert_message = "Closed Short")
strategy.exit("exit short", from_entry="S2", qty=2, profit= targetS2, stop = shortStopPrice, alert_message = "Closed Short")
strategy.exit("exit short", from_entry="S3", qty=2, profit= targetS3, stop = shortStopPrice, alert_message = "Closed Short")

//cancel short scales if position closed
if strategy.position_size[1] < 0 and strategy.position_size >= 0
   strategy.cancel("S2")
    strategy.cancel("S3")


///////////////////////////////////////////////////
//close and cancel all eod
//if closealltime
//    strategy.close_all(alert_message= "Closed All Trades")

//if cancelalltime
// strategy.cancel_all()


///////////////////////////////////////////////////
// Visualization

hline(	3880.51	, color=color.blue, linestyle=hline.style_solid)
hline(	3893.57	, color=color.blue, linestyle=hline.style_solid)
hline(	3906.64	, color=color.blue, linestyle=hline.style_solid)
hline(	3919.70	, color=color.blue, linestyle=hline.style_solid)
hline(	3932.77	, color=color.blue, linestyle=hline.style_solid)
hline(	3945.83	, color=color.blue, linestyle=hline.style_solid)
hline(	3958.90	, color=color.blue, linestyle=hline.style_solid)
hline(	3971.96	, color=color.blue, linestyle=hline.style_solid)
hline(	3985.03	, color=color.blue, linestyle=hline.style_solid)
hline(	3998.09	, color=color.blue, linestyle=hline.style_solid)
hline(	4011.16	, color=color.blue, linestyle=hline.style_solid)
hline(	4024.22	, color=color.blue, linestyle=hline.style_solid)
hline(	4037.29	, color=color.blue, linestyle=hline.style_solid)
hline(	4050.35	, color=color.blue, linestyle=hline.style_solid)
hline(	4063.42	, color=color.blue, linestyle=hline.style_solid)
hline(	4076.48	, color=color.blue, linestyle=hline.style_solid)
hline(	4089.55	, color=color.blue, linestyle=hline.style_solid)
hline(	4102.61	, color=color.blue, linestyle=hline.style_solid)
hline(	4115.68	, color=color.blue, linestyle=hline.style_solid)
hline(	4128.74	, color=color.blue, linestyle=hline.style_solid)
hline(	4141.81	, color=color.blue, linestyle=hline.style_solid)
hline(	4154.87	, color=color.blue, linestyle=hline.style_solid)
hline(	4167.94	, color=color.blue, linestyle=hline.style_solid)
hline(	4181.00	, color=color.blue, linestyle=hline.style_solid)
hline(	4194.07	, color=color.blue, linestyle=hline.style_solid)
hline(	4207.13	, color=color.blue, linestyle=hline.style_solid)
hline(	4220.20	, color=color.blue, linestyle=hline.style_solid)
hline(	4233.26	, color=color.blue, linestyle=hline.style_solid)
hline(	4246.33	, color=color.blue, linestyle=hline.style_solid)
hline(	4259.39	, color=color.blue, linestyle=hline.style_solid)
hline(	4272.46	, color=color.blue, linestyle=hline.style_solid)
hline(	4285.52	, color=color.blue, linestyle=hline.style_solid)
hline(	4298.59	, color=color.blue, linestyle=hline.style_solid)
hline(	4311.65	, color=color.blue, linestyle=hline.style_solid)
hline(	4324.72	, color=color.blue, linestyle=hline.style_solid)
hline(	4337.78	, color=color.blue, linestyle=hline.style_solid)
hline(	4350.85	, color=color.blue, linestyle=hline.style_solid)
hline(	4363.91	, color=color.blue, linestyle=hline.style_solid)
hline(	4376.97	, color=color.blue, linestyle=hline.style_solid)
