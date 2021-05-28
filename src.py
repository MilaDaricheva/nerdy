// This source code is subject to the terms of the Mozilla Public License 2.0 at https: // mozilla.org/MPL/2.0/
// © auntmotya

//@version = 4
strategy("VP-Strategy-Nerdy", overlay=true, pyramiding=5, initial_capital=50000, calc_on_every_tick=false, currency="USD", default_qty_value=1)
//equal longs and shorts, somewhat

///////////////////////////////////////////////////
// Backtest inputs
FromMonth = input(defval=4, title="From Month", minval=1, maxval=12)
FromDay = input(defval=1, title="From Day", minval=1, maxval=31)
FromYear = input(defval=2021, title="From Year", minval=2021)

ToMonth = input(defval=5, title="To Month", minval=1, maxval=12)
ToDay = input(defval=30, title="To Day", minval=1, maxval=31)
ToYear = input(defval=2022, title="To Year", minval=2017)

// Define backtest timewindow
start = timestamp(FromYear, FromMonth, FromDay, 00, 00) // backtest start window
finish = timestamp(ToYear, ToMonth, ToDay, 23, 59) // backtest finish window

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
// hist_data.py

ema30 = ema(close, 540)
emaUp = ema30 > ema30[60]
emaDown = ema30 < ema30[60]
//plotchar(emaUp, "emaUp", "", location.top)
//plotchar(emaDown, "emaDown", "", location.top)

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

onlyLongs = (bigK < 20 or bigD < 25 or InLongB)
onlyShorts = (bigK > 85 or bigD > 85 or InShortB)

noLongs = bigK > 90 or bigD > 90
noShorts = bigK < 25 or bigD < 25

//plotchar(onlyLongs, "onlyLongs", "", location.top)
//plotchar(onlyShorts, "onlyShorts", "", location.top)


///////////////////////////////////////////////////
// Entry & Exit signals
var float rememberVPlevel = aroundVPLevel
if rememberVPlevel[1] != aroundVPLevel and aroundVPLevel > 0
rememberVPlevel := aroundVPLevel

//plotchar(rememberVPlevel, "rememberVPlevel", "", location.top)

//order_management.py

flipLong = false
//Close shorts
if strategy.position_size < 0 and (aroundVPLevel > 0) and (aroundVPLevel[1] > 0) and aroundVPLevelToShort == 0
if ((not noLongs and (bigK < 10 or bigD < 10 or InLongB)) or emaUp) and (bigD < 90)
strategy.close_all(comment="Closed all Shorts", alert_message="Closed all Shorts")
flipLong := true

canTrade = (time >= start) and (time <= finish) and (strategy.position_size == 0) and not whatstime

inLongTime = strategy.position_size > 0

timeInLongTrade = barssince(not inLongTime)

//plotchar(timeInLongTrade, "timeInLongTrade", "", location.top)

//Start Long
if (canTrade or flipLong) and aroundVPLevel > 0 and aroundVPLevelToShort == 0 and ((onlyLongs and not noLongs) or emaUp)
strategy.entry("L1", strategy.long, 1, alert_message="Started Long")
strategy.entry("L2", strategy.long, 2, limit=rememberVPlevel - 4, alert_message="Added Long")
strategy.entry("L3", strategy.long, 2, limit=rememberVPlevel - 10, alert_message="Added Long")

//2d3d Scale updated
//if strategy.position_size == 1 and timeInLongTrade > 150 and aroundVPLevel > 0 and aroundVPLevelToShort == 0
// strategy.entry("L2", strategy.long, 2, limit=rememberVPlevel, alert_message="Added Long")
// strategy.entry("L3", strategy.long, 2, limit=rememberVPlevel, alert_message="Added Long")


//cancel scales if position closed
if strategy.position_size[1] > 0 and strategy.position_size <= 0
strategy.cancel("L2")
strategy.cancel("L3")

target2 = 40
target3 = 80

// Determine stop loss prices
longStopPrice = rememberVPlevel - 22

if emaDown and emaDown[60]
longStopPrice := rememberVPlevel - 13
if strategy.position_size == 5
target2 := 16
target3 := 40

//tight stop for full pos after 410 min and onlyShort
if strategy.position_size == 5 and timeInLongTrade > 410
longStopPrice := strategy.position_avg_price

//stop tight after scale out
if strategy.position_size[1] == 5 and strategy.position_size == 3
longStopPrice := strategy.position_avg_price - 10
if strategy.position_size[1] == 3 and strategy.position_size == 1
longStopPrice := strategy.position_avg_price
//if strategy.position_size == 1 and close > 30 + strategy.position_avg_price
// longStopPrice := strategy.position_avg_price + (close - strategy.position_avg_price)/2 - 10

//should never get bigger during the open trade
if longStopPrice < longStopPrice[1] and strategy.position_size > 0 and timeInLongTrade > 5
longStopPrice := longStopPrice[1]

plotchar(longStopPrice, "longStopPrice", "", location.top)


strategy.exit("exit long", from_entry="L1", qty=1, profit=300, stop=longStopPrice, alert_message="Closed Long")
strategy.exit("exit long", from_entry="L2", qty=2, profit=target2, stop=longStopPrice, alert_message="Closed Long")
strategy.exit("exit long", from_entry="L3", qty=2, profit=target3, stop=longStopPrice, alert_message="Closed Long")


///////////////////////////////////////////////////
// Short Entries

var float rememberVPlevelShort = aroundVPLevelToShort
if rememberVPlevelShort[1] != aroundVPLevelToShort and aroundVPLevelToShort > 0
rememberVPlevelShort := aroundVPLevelToShort

//plotchar(rememberVPlevelShort, "rememberVPlevelShort", "", location.top)

canShort = (time >= start) and (time <= finish) and (strategy.position_size == 0) and not whatstime

flipShort = false

inShortTime = strategy.position_size < 0

timeInShortTrade = barssince(not inShortTime)
//plotchar(timeInShortTrade, "timeInShortTrade", "", location.top)
//plotchar(low, "low", "", location.top)
//plotchar(ema30, "ema30", "", location.top)

//order_management.py

//Close longs
if strategy.position_size > 0 and aroundVPLevelToShort > 0 and aroundVPLevelToShort[1] > 0
if (not (emaUp and onlyLongs) and ((not noShorts and onlyShorts) or emaDown)) or (onlyShorts and low < ema30 + 1)
strategy.close_all(comment="Closed All Longs", alert_message="Closed All Longs")
flipShort := true

//Start Short
if (canShort or flipShort) and aroundVPLevelToShort > 0 and aroundVPLevel == 0
if (not (emaUp and onlyLongs) and ((not noShorts and onlyShorts) or emaDown)) or (onlyShorts and low < ema30 + 1)
strategy.entry("S1", strategy.short, 1, alert_message="Started Short")
strategy.entry("S2", strategy.short, 2, limit=rememberVPlevelShort + 3, alert_message="Added Short")
strategy.entry("S3", strategy.short, 2, limit=rememberVPlevelShort + 10, alert_message="Added Short")

//2d3d Scale updated
//if strategy.position_size == -1 and timeInShortTrade > 150 and aroundVPLevel == 0 and aroundVPLevelToShort > 0
// strategy.entry("S2", strategy.short, 2, limit=rememberVPlevelShort, alert_message="Added Short")
// strategy.entry("S3", strategy.short, 2, limit=rememberVPlevelShort, alert_message="Added Short")

//cancel short scales if position closed
if strategy.position_size[1] < 0 and strategy.position_size >= 0
strategy.cancel("S2")
strategy.cancel("S3")


//Stop Price
shortStopPrice = rememberVPlevelShort + 22

targetS2 = 40
targetS3 = 80

if emaUp and emaUp[60] and InLongB
shortStopPrice := rememberVPlevelShort + 13
if strategy.position_size == -5
targetS2 := 16
targetS3 := 40

//tight stop for full pos after 240 min and onlyLongs
if strategy.position_size == -5 and timeInShortTrade > 410
shortStopPrice := strategy.position_avg_price

//stop tight after scale out
if strategy.position_size[1] == -5 and strategy.position_size == -3
shortStopPrice := strategy.position_avg_price + 10
if strategy.position_size[1] == -3 and strategy.position_size == -1
shortStopPrice := strategy.position_avg_price


//should never get bigger during the open trade
if shortStopPrice > shortStopPrice[1] and strategy.position_size < 0 and timeInShortTrade > 5
shortStopPrice := shortStopPrice[1]

plotchar(shortStopPrice, "shortStopPrice", "", location.top)
//plotchar(timeInShortTrade, "timeInShortTrade", "", location.top)

strategy.exit("exit short", from_entry="S1", qty=1, profit=150, stop=shortStopPrice, alert_message="Closed Short")
strategy.exit("exit short", from_entry="S2", qty=2, profit=targetS2, stop=shortStopPrice, alert_message="Closed Short")
strategy.exit("exit short", from_entry="S3", qty=2, profit=targetS3, stop=shortStopPrice, alert_message="Closed Short")

//close and cancel all eod
if closealltime
strategy.close_all(alert_message="Closed All Trades")

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
