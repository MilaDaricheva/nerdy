// This source code is subject to the terms of the Mozilla Public License 2.0 at https: // mozilla.org/MPL/2.0/
// © auntmotya

//@version = 4
strategy("Nerdy-1000", overlay=true, pyramiding=4, initial_capital=50000, calc_on_every_tick=false, currency="USD", default_qty_value=1)
//new rules new lines

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

//plotchar(lowestLow, "lowestLow", "", location.top)
//plotchar(highestHighBig, "highestHighBig", "", location.top)

///////////////////////////////////////////////////
// Generate array of VP
// demo.py init

lenMainVP = 55
float[] mainVP = array.new_float(0)
sVP = 4249.63
step = 14.955

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

//plotchar(rememberVPlevelShort, "rememberVPlevelShort", "", location.top)

///////////////////////////////////////////////////
// Time Management
timeinrange(res, sess) = > not na(time(res, sess)) ? 1: 0

whatstime = timeinrange("1", "1500-1705:123456")
//plotchar(whatstime, "whatstime", "", location.top)

closealltime = timeinrange("1", "1509-1511:6")
//plotchar(closealltime, "closealltime", "", location.top)

cancelalltime = timeinrange("1", "1513-1515:6")
//plotchar(cancelalltime, "cancelalltime", "", location.top)


///////////////////////////////////////////////////
// Steps strategy_management.py
oneStepsFromHigh = highestHighBig - low > 0.85*step
oneStepsFromLow = high - lowestLowBig > 0.85*step

twoStepsFromHigh = highestHighBig - low > 1.8*step
twoStepsFromLow = high - lowestLowBig > 1.8*step

threeStepsFromHigh = highestHighBig - low > 2.8*step
threeStepsFromLow = high - lowestLowBig > 2.8*step

fourStepsFromHigh = highestHighBig - low > 3.7*step
fourStepsFromLow = high - lowestLowBig > 3.7*step

fiveStepsFromHigh = highestHighBig - low > 4.7*step
fiveStepsFromLow = high - lowestLowBig > 4.7*step

sixStepsFromHigh = highestHighBig - low > 5.7*step
sixStepsFromLow = high - lowestLowBig > 5.7*step

//plotchar(oneStepsFromHigh, "oneStepsFromHigh", "", location.top)
//plotchar(oneStepsFromLow, "oneStepsFromLow", "", location.top)
//plotchar(twoStepsFromHigh, "twoStepsFromHigh", "", location.top)
//plotchar(twoStepsFromLow, "twoStepsFromLow", "", location.top)
//plotchar(threeStepsFromHigh, "threeStepsFromHigh", "", location.top)
//plotchar(threeStepsFromLow, "threeStepsFromLow", "", location.top)
//plotchar(fourStepsFromHigh, "fourStepsFromHigh", "", location.top)
//plotchar(fourStepsFromLow, "fourStepsFromLow", "", location.top)
//plotchar(fiveStepsFromHigh, "fiveStepsFromHigh", "", location.top)
//plotchar(fiveStepsFromLow, "fiveStepsFromLow", "", location.top)
//plotchar(sixStepsFromHigh, "sixStepsFromHigh", "", location.top)
//plotchar(sixStepsFromLow, "sixStepsFromLow", "", location.top)

///////////////////////////////////////////////////
// EMA
// hist_data.py  strategy_management.py

ema30 = ema(close, 540)
emaUp = ema30 > ema30[60]
emaDown = ema30 < ema30[60]
emaDiff = ema30 - ema30[120]

emaD0 = emaDiff < 0.7 and emaDiff > -0.7
emaD1 = emaDiff < 1 and emaDiff > -1
emaD2 = emaDiff < 2 and emaDiff > -2
emaD3 = emaDiff < 3 and emaDiff > -3
emaD4 = emaDiff < 4 and emaDiff > -4
emaD5 = emaDiff < 5 and emaDiff > -5
emaD6 = emaDiff < 6 and emaDiff > -6
emaD10 = emaDiff < 10 and emaDiff > -10

//plotchar(emaDiff, "emaDiff", "", location.top)

bigEmaExpr = ema(close, 200)
bigEmaVal = security(syminfo.tickerid, "60", bigEmaExpr)

downtrend = bigEmaVal + 15 > close

//plotchar(bigEmaVal, "bigEmaVal", "", location.top)

///////////////////////////////////////////////////
// Entry & Exit signals. strategy_management.py
slowestCond = oneStepsFromHigh and emaD0

wobbleCond = twoStepsFromHigh and emaD2

trendCond = threeStepsFromHigh and emaD3

strongCond = fourStepsFromHigh and emaD6

extremeCond = fiveStepsFromHigh and not emaD6


//order_management.py


cond1 = twoStepsFromHigh and emaUp
cond2 = (wobbleCond or trendCond or strongCond or extremeCond) and emaDown

canTrade = strategy.position_size == 0 and not whatstime

inLongTime = strategy.position_size > 0

timeInLongTrade = barssince(not inLongTime)

//plotchar(timeInLongTrade, "timeInLongTrade", "", location.top)

//Start Long
if (canTrade and aroundVPLevel > 0)
   if cond1 or cond2
       if emaDiff > -4 and emaDiff < 0
           if not downtrend
               strategy.entry("L0", strategy.long, 1, limit=rememberVPlevel, alert_message="Started Long")
                strategy.entry("L1", strategy.long, 1, limit=rememberVPlevel, alert_message="Added Long")
                strategy.entry("L2", strategy.long, 1, limit=rememberVPlevel - 13, alert_message="Added Long")
                strategy.entry("L3", strategy.long, 1, limit=rememberVPlevel - 13, alert_message="Added Long")
            if downtrend
               strategy.entry("L0", strategy.long, 1, limit=rememberVPlevel - 12, alert_message="Started Long")
                strategy.entry("L1", strategy.long, 1, limit=rememberVPlevel - 12, alert_message="Added Long")
                strategy.entry("L2", strategy.long, 1, limit=rememberVPlevel - 25, alert_message="Added Long")
                strategy.entry("L3", strategy.long, 1, limit=rememberVPlevel - 25, alert_message="Added Long")
        if emaDiff > 0
           if not downtrend
               strategy.entry("L0", strategy.long, 1, alert_message = "Started Long")
                strategy.entry("L1", strategy.long, 1, alert_message= "Added Long")
                strategy.entry("L2", strategy.long, 1, limit= rememberVPlevel - 4, alert_message = "Added Long")
                strategy.entry("L3", strategy.long, 1, limit= rememberVPlevel - 6, alert_message = "Added Long")
            if downtrend
               strategy.entry("L0", strategy.long, 1, limit=rememberVPlevel - 12, alert_message="Started Long")
                strategy.entry("L1", strategy.long, 1, limit=rememberVPlevel - 12, alert_message="Added Long")
                strategy.entry("L2", strategy.long, 1, limit=rememberVPlevel - 25, alert_message="Added Long")
                strategy.entry("L3", strategy.long, 1, limit=rememberVPlevel - 25, alert_message="Added Long")

    else
       if slowestCond or (emaDiff > 1 and oneStepsFromHigh)
           if not downtrend
               strategy.entry("L0", strategy.long, 1, alert_message = "Started Long")
                strategy.entry("L1", strategy.long, 1, alert_message= "Added Long")
                strategy.entry("L2", strategy.long, 1, limit= rememberVPlevel - 4, alert_message = "Added Long")
                strategy.entry("L3", strategy.long, 1, limit= rememberVPlevel - 6, alert_message = "Added Long")
            if downtrend
               strategy.entry("L0", strategy.long, 1, limit=rememberVPlevel - 12, alert_message="Started Long")
                strategy.entry("L1", strategy.long, 1, limit=rememberVPlevel - 12, alert_message="Added Long")
                strategy.entry("L2", strategy.long, 1, limit=rememberVPlevel - 25, alert_message="Added Long")
                strategy.entry("L3", strategy.long, 1, limit=rememberVPlevel - 25, alert_message="Added Long")

chartURL = "https://www.tradingview.com/chart/lAXDOGpR/#"
jsonSTR = "{" + "\"embeds\":[{\"title\":\"" + "TradingView chart" + "\",\"url\":\"" + chartURL + "\"}]}"
openedTradeCondition = strategy.position_size[1] == 0 and strategy.position_size > 0
if openedTradeCondition
   alert(jsonSTR, alert.freq_once_per_bar)


target0 = 90
target1 = 40

target2 = 40
target3 = 56


// Determine stop loss prices
longStopPrice = rememberVPlevel - 20

if downtrend
   longStopPrice := rememberVPlevel - 30

//should never get bigger during the open trade
if longStopPrice < longStopPrice[1] and strategy.position_size > 0 and timeInLongTrade > 5
   longStopPrice := longStopPrice[1]


plotchar(longStopPrice, "longStopPrice", "", location.top)

strategy.exit("exit long", from_entry="L0", qty=1, profit=target0, stop = longStopPrice, alert_message = "Scaled Out Long")
strategy.exit("exit long", from_entry="L1", qty=1, profit=target1, stop = longStopPrice, alert_message = "Scaled Out Long")
strategy.exit("exit long", from_entry="L2", qty=1, profit=target2, stop = longStopPrice, alert_message = "Scaled Out Long")
strategy.exit("exit long", from_entry="L3", qty=1, profit=target3, stop = longStopPrice, alert_message = "Scaled Out Long")


//demo.py
//cancel scales if position closed
if strategy.position_size[1] > 0 and strategy.position_size <= 0
   strategy.cancel("L0")
    strategy.cancel("L1")
    strategy.cancel("L2")
    strategy.cancel("L3")


///////////////////////////////////////////////////
// Short Conditions

wobbleCondS = twoStepsFromLow and emaD1

trendCondS = threeStepsFromLow and emaD4 and not emaD1

strongCondS = fourStepsFromLow and not emaD4 and emaD5

extremeCondS = fiveStepsFromLow and not emaD5


lastDump = barssince(sixStepsFromHigh) // to bucket.py

if not lastDump
   if lastDump[1] > 0
       lastDump := lastDump[1] + 1
    else
       lastDump := 1441

//plotchar(lastDump, "lastDump", "", location.top)


canShort = strategy.position_size == 0 and not whatstime

inShortTime = strategy.position_size < 0

timeInShortTrade = barssince(not inShortTime)

//plotchar(timeInShortTrade, "timeInShortTrade", "", location.top)

//order_management.py
condS1 = (twoStepsFromLow and emaDown and lastDump > 1440)
condS2 = ((wobbleCondS or trendCondS or strongCondS or extremeCondS) and emaUp and lastDump > 1440)

//Close longs
if strategy.position_size > 0 and aroundVPLevelToShort > 0
   if condS1 or condS2
       if (emaDiff < -0.7 or trendCondS) and aroundVPLevelToShort[1] > 0
           strategy.close_all(comment = "Closed All Longs", alert_message = "Closed All Longs")
    if emaDiff < -5
       strategy.close_all(comment = "Closed All Longs", alert_message = "Closed All Longs")

///////////////////////////////////////////////////
//close and cancel all eod
if closealltime
   strategy.close_all(alert_message = "Closed All Trades")

if cancelalltime
   strategy.cancel_all()


///////////////////////////////////////////////////
// Visualization
hline(	4339.36	, color=color.blue, linestyle=hline.style_solid)
hline(	4324.40	, color=color.blue, linestyle=hline.style_solid)
hline(	4309.45	, color=color.blue, linestyle=hline.style_solid)
hline(	4294.49	, color=color.blue, linestyle=hline.style_solid)
hline(	4279.54	, color=color.blue, linestyle=hline.style_solid)
hline(	4264.58	, color=color.blue, linestyle=hline.style_solid)
hline(	4249.63	, color=color.blue, linestyle=hline.style_solid)

hline(	4354.31	, color=color.blue, linestyle=hline.style_solid)
hline(	4369.27	, color=color.blue, linestyle=hline.style_solid)
hline(	4384.22	, color=color.blue, linestyle=hline.style_solid)
hline(	4399.18	, color=color.blue, linestyle=hline.style_solid)
hline(	4414.13	, color=color.blue, linestyle=hline.style_solid)
hline(	4429.09	, color=color.blue, linestyle=hline.style_solid)
hline(	4444.04	, color=color.blue, linestyle=hline.style_solid)
hline(	4459.00	, color=color.blue, linestyle=hline.style_solid)
hline(	4473.95	, color=color.blue, linestyle=hline.style_solid)
hline(	4488.91	, color=color.blue, linestyle=hline.style_solid)
hline(	4503.86	, color=color.blue, linestyle=hline.style_solid)
hline(	4518.82	, color=color.blue, linestyle=hline.style_solid)
hline(	4533.77	, color=color.blue, linestyle=hline.style_solid)
hline(	4548.73	, color=color.blue, linestyle=hline.style_solid)
hline(	4563.68	, color=color.blue, linestyle=hline.style_solid)
hline(	4578.64	, color=color.blue, linestyle=hline.style_solid)
hline(	4593.59	, color=color.blue, linestyle=hline.style_solid)
hline(	4608.55	, color=color.blue, linestyle=hline.style_solid)
hline(	4623.50	, color=color.blue, linestyle=hline.style_solid)
hline(	4638.46	, color=color.blue, linestyle=hline.style_solid)
hline(	4653.41	, color=color.blue, linestyle=hline.style_solid)
hline(	4668.37	, color=color.blue, linestyle=hline.style_solid)
hline(	4683.32	, color=color.blue, linestyle=hline.style_solid)
hline(	4698.28	, color=color.blue, linestyle=hline.style_solid)
hline(	4713.23	, color=color.blue, linestyle=hline.style_solid)
hline(	4728.19	, color=color.blue, linestyle=hline.style_solid)
hline(	4743.14	, color=color.blue, linestyle=hline.style_solid)
hline(	4758.10	, color=color.blue, linestyle=hline.style_solid)
hline(	4773.05	, color=color.blue, linestyle=hline.style_solid)
hline(	4788.01	, color=color.blue, linestyle=hline.style_solid)
hline(	4802.96	, color=color.blue, linestyle=hline.style_solid)
hline(	4817.92	, color=color.blue, linestyle=hline.style_solid)
hline(	4832.87	, color=color.blue, linestyle=hline.style_solid)
hline(	4847.83	, color=color.blue, linestyle=hline.style_solid)
hline(	4862.78	, color=color.blue, linestyle=hline.style_solid)
hline(	4877.74	, color=color.blue, linestyle=hline.style_solid)
hline(	4892.69	, color=color.blue, linestyle=hline.style_solid)
hline(	4907.65	, color=color.blue, linestyle=hline.style_solid)
hline(	4922.60	, color=color.blue, linestyle=hline.style_solid)
hline(	4937.56	, color=color.blue, linestyle=hline.style_solid)
hline(	4952.51	, color=color.blue, linestyle=hline.style_solid)
hline(	4967.47	, color=color.blue, linestyle=hline.style_solid)
hline(	4982.42	, color=color.blue, linestyle=hline.style_solid)
hline(	4997.38	, color=color.blue, linestyle=hline.style_solid)
hline(	5012.33	, color=color.blue, linestyle=hline.style_solid)
hline(	5027.29	, color=color.blue, linestyle=hline.style_solid)
hline(	5042.24	, color=color.blue, linestyle=hline.style_solid)
hline(	5057.20	, color=color.blue, linestyle=hline.style_solid)
hline(	5072.15	, color=color.blue, linestyle=hline.style_solid)
hline(	5087.11	, color=color.blue, linestyle=hline.style_solid)
