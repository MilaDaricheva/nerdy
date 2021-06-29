// This source code is subject to the terms of the Mozilla Public License 2.0 at https: // mozilla.org/MPL/2.0/
// © auntmotya

//@version = 4
strategy("VP-Strategy-Nerdy", overlay=true, pyramiding=5, initial_capital=50000, calc_on_every_tick=false, currency="USD", default_qty_value=1)
//new rules


///////////////////////////////////////////////////
// Last bars low maybe 60 is better
// hist_data.py
lowestLow = lowest(low, 60)

// Last bars high
highestHigh = highest(high, 60)

///////////////////////////////////////////////////
// Generate array of VP
// demo.py init

lenMainVP = 50
float[] mainVP = array.new_float(0)
sVP = 3880.51

for i = 0 to lenMainVP-1
   array.push(mainVP, sVP)
    sVP := sVP+13.065

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

//plotchar(rememberVPlevelShort, "rememberVPlevelShort", "", location.top)

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
// EMA
// hist_data.py  strategy_management.py

ema30 = ema(close, 540)
emaUp = ema30 > ema30[60]
emaDown = ema30 < ema30[60]
emaDiff = ema30 - ema30[120]
//plotchar(emaDiff, "ema dif", "", location.top)
//plotchar(emaDown, "emaDown", "", location.top)

emaNearLong = ema30 > aroundVPLevel and ema30 < aroundVPLevel + 2
emaNearShort = ema30 < aroundVPLevelToShort and ema30 > aroundVPLevelToShort - 2


///////////////////////////////////////////////////
// Big TimeFrame
// hist_data.py

bigTimeFrame = close
bigRsiL = rsi(bigTimeFrame, 420)
bigStoch = stoch(bigRsiL, bigRsiL, bigRsiL, 420)
bigK = sma(bigStoch, 90)
bigD = sma(bigK, 90)


InLongB = false
InShortB = false
DiffSensB = 1
EnterLongB = bigK > bigD + DiffSensB and bigK[1] <= bigD[1] + DiffSensB and not InLongB[1]
EnterShortB = bigK < bigD - DiffSensB and bigK[1] >= bigD[1] - DiffSensB and not InShortB[1]
InLongB := EnterLongB or InLongB[1] and not EnterShortB
InShortB := EnterShortB or InShortB[1] and not EnterLongB

//plotchar(InLongB, "InLongB", "", location.top)
//plotchar(InShortB, "InShortB", "", location.top)
//plotchar(bigK, "bigK", "", location.top)
//plotchar(bigD, "bigD", "", location.top)

//strategy_management.py

onlyLongs = (emaUp or InLongB)
onlyShorts = (emaDown or InShortB)

noLongs = bigK > 50 or bigD > 50
noShorts = bigK < 50 or bigD < 50

tooHigh = bigK > 80 or bigD > 80
tooLow = bigK < 21 or bigD < 21

//plotchar(onlyLongs, "onlyLongs", "", location.top)
//plotchar(onlyShorts, "onlyShorts", "", location.top)
//plotchar(noLongs, "noLongs", "", location.top)
//plotchar(noShorts, "noShorts", "", location.top)

///////////////////////////////////////////////////
// Entry & Exit signals


//order_management.py

flipLong = false
//Close shorts
if strategy.position_size < 0 and aroundVPLevel > 0 and aroundVPLevelToShort == 0
   if ((onlyLongs and not noLongs and InLongB) or noShorts) and not (emaNearLong and InShortB)
       strategy.close_all(comment="Closed all Shorts", alert_message="Closed all Shorts")
        flipLong := true
        strategy.cancel("S2")
        strategy.cancel("S3")

canTrade = strategy.position_size == 0 and not whatstime

inLongTime = strategy.position_size > 0

timeInLongTrade = barssince(not inLongTime)

//plotchar(timeInLongTrade, "timeInLongTrade", "", location.top)

//Start Long
if (canTrade and aroundVPLevel > 0 and aroundVPLevelToShort == 0) or flipLong[1]
   if emaDiff > -0.55 and emaDiff < 0.55 and noShorts and not (emaNearLong and InShortB)
        strategy.entry("L1", strategy.long, 1, alert_message="Started Long")
        strategy.entry("L2", strategy.long, 2, limit=rememberVPlevel - 4, alert_message="Added Long")
        strategy.entry("L3", strategy.long, 2, limit=rememberVPlevel - 10, alert_message="Added Long")
    else if ((onlyLongs and not noLongs and InLongB) or noShorts) and not (emaNearLong and InShortB)
        strategy.entry("L1", strategy.long, 1, alert_message = "Started Long")
        if not onlyShorts
            strategy.entry("L2", strategy.long, 2, limit = rememberVPlevel - 4, alert_message = "Added Long")
            strategy.entry("L3", strategy.long, 2, limit = rememberVPlevel - 10, alert_message = "Added Long")


target1 = 120
target2 = 40
target3 = 80

// Determine stop loss prices
longStopPrice = rememberVPlevel - 22

if strategy.position_size > 0 and onlyShorts
   longStopPrice := rememberVPlevel - 14
    target3 := 40
    strategy.cancel("L2")
    strategy.cancel("L3")

//Tight stop for a runner
//if strategy.position_size > 0 and aroundVPLevelToShort > 0 and strategy.position_avg_price < aroundVPLevelToShort - 20
// longStopPrice := aroundVPLevelToShort - 8

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


canShort = strategy.position_size == 0 and not whatstime

flipShort = false

inShortTime = strategy.position_size < 0

timeInShortTrade = barssince(not inShortTime)

//order_management.py

//Close longs
if strategy.position_size > 0 and aroundVPLevelToShort > 0
   if emaDiff > -0.55 and emaDiff < 0.55 and noLongs
       strategy.close_all(comment = "Closed All Longs", alert_message = "Closed All Longs")
        flipShort := true
        strategy.cancel("L2")
        strategy.cancel("L3")
    else if (onlyShorts and not noShorts and not onlyLongs) or (InShortB and emaNearShort)
       strategy.close_all(comment = "Closed All Longs", alert_message = "Closed All Longs")
        flipShort := true
        strategy.cancel("L2")
        strategy.cancel("L3")

//Start Short
if (canShort and aroundVPLevelToShort > 0 and aroundVPLevel == 0) or flipShort[1]
    if emaDiff > -0.55 and emaDiff < 0.55 and noLongs
        strategy.entry("S1", strategy.short, 1, alert_message = "Started Short")
        strategy.entry("S2", strategy.short, 2, limit= rememberVPlevelShort + 3, alert_message = "Added Short")
        strategy.entry("S3", strategy.short, 2, limit= rememberVPlevelShort + 10, alert_message = "Added Short")
    else if (onlyShorts and not noShorts and not onlyLongs) or (InShortB and emaNearShort and not noShorts)
        strategy.entry("S1", strategy.short, 1, alert_message = "Started Short")
        if not onlyLongs
           strategy.entry("S2", strategy.short, 2, limit = rememberVPlevelShort + 3, alert_message = "Added Short")
            strategy.entry("S3", strategy.short, 2, limit= rememberVPlevelShort + 10, alert_message = "Added Short")


//cancel short scales if position closed
if strategy.position_size[1] < 0 and strategy.position_size >= 0
   strategy.cancel("S2")
    strategy.cancel("S3")


//Stop Price
shortStopPrice = rememberVPlevelShort + 22

targetS1 = 120
if targetS1[1] < targetS1
   targetS1 := targetS1[1]
targetS2 = 40
targetS3 = 80

if strategy.position_size < 0 and onlyLongs
   shortStopPrice := rememberVPlevelShort + 18
    targetS1 := 40
    targetS2 := 16
    targetS3 := 40
    //strategy.cancel("S2")
    //strategy.cancel("S3")

//if strategy.position_size < 0 and onlyLongs and aroundVPLevel > 0
// shortStopPrice := rememberVPlevelShort + 14

//Tight stop for a runner
//if strategy.position_size < 0 and aroundVPLevel > 0 and strategy.position_avg_price > aroundVPLevel + 20
// shortStopPrice := aroundVPLevel + 6


//should never get bigger during the open trade
if shortStopPrice > shortStopPrice[1] and strategy.position_size < 0 and timeInShortTrade > 5
   shortStopPrice := shortStopPrice[1]

plotchar(shortStopPrice, "shortStopPrice", "", location.top)
//plotchar(timeInShortTrade, "timeInShortTrade", "", location.top)

strategy.exit("exit short", from_entry="S1", qty=1, profit= targetS1, stop = shortStopPrice, alert_message = "Closed Short")
strategy.exit("exit short", from_entry="S2", qty=2, profit= targetS2, stop = shortStopPrice, alert_message = "Closed Short")
strategy.exit("exit short", from_entry="S3", qty=2, profit= targetS3, stop = shortStopPrice, alert_message = "Closed Short")

//close and cancel all eod
if closealltime
   strategy.close_all(alert_message = "Closed All Trades")

if cancelalltime
   strategy.cancel_all()


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
