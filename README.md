AI-Trading-Bot
Automatic Trading Bot based on AI-based indicators.

**Is it time to enter a position? What is the challenge?**

While both of them is a core question for an automatic trading bot, "Is it time to enter a position?" is more important than "Is it time to exit the position?", as exiting a position has two obvious scenarios: Take Profit and Stop Loss. Entering a position, however, requires your confidence that the position will have chance to be existed with profit in the near future.

Let's think of a simple enter-and-exit round of trading, which is a buy-and-sell round in spot markets. 

An example is 
- starting from possessing a origianal quote amount 5,000 USDT, 
- entering a position: buying a base amount 2.0 ETH for the quote amount of 5,000 USDT at the ETH/USDT price of 2,500,
- exiting the position: selling back the base amount 2.0 ETH for a new quote amount (original 5,000 + profit) USDT at a higher ETH/USDT price,
- and settling the profit.

(The following section is depicted in https://fleetpro.medium.com/is-it-time-to-enter-a-position-832b7628715f )

We know that

Net Profit for a round 
= ( % total price change - % decision cost - % price slippage - % exchange fees ) 
   X (times) original quote amount,

where 
- % denotes the percentage over the original quote quantity that was possessed before entering,
- Total Price Change (TPC) is the price difference between the the start of a up-trending and its following start of down-trending. It's ideal to enter or exit right at these starts of trending. We want to challenge to predict TPC.
- Decision Cost (DC) is the price change monitored/consumed, after the starts of trending, to finally decide on entry/exit. It's practical to inevitably consume/waste some price change before entry/exit, although it compromises the net profit badly. We want to avoid or reduce DC.
- price slippage, incurred due to limited liquidity, is the price difference between the buy/sell order and its actual fulfilling transaction. % price slippage is negligible  if not a small constant. We don't care of slippage.
- and exchange fees are the fees paid to the exchange on buying and selling. % exchange fees are constant. We accept and make up for fees.

An example is

Net Profit 
= ( % TPC - % DC - % slippage - % fees ) X (times) original amount
= (%TPC - 0.07% x 2–0.1% x 2–0.5% x 2) X (original 5,000 USDT) = (%TPC - 1.34% ) x 5,000 USDT,

where they are all multiplied by 2 because there are two exchange actions: enter and exit.
It seems that the least indicator that we need should answer the question "Will be there a price change of over 1.34%, in the near future?" or, in general,

"Will be there a price change of over X% within Y time period?",

where X and Y should be optimized for an aimed performance. For example, X should be larger to make up for losses incurred by failed rounds, and Y should be smaller to have more frequent rounds and to avoid the effect of external happenings.

Examples are: There will be a price change of over 3% in 48 hours, 3% in 6 hours, and 2% in 3 hours, each with a certain confidence.

The common sense logic in frequency trading, explicit or implicit, is:

- If we have a solid prediction that we are having a TPC that is large enough, then we can enter a position now, thus saving the decision cost. This is an ideal solution.
- Even if we have a weak prediction of that, we bravely enter a position all in the hope of luck. This is something we must avoid doing.
- Else if we have a weak prediction of that, then we try to make up for the weakness with additional confidence gained by monitoring/consuming more price change, thus incurring the decision cost. If successful, the we enter a position. This is a practical and common solution.
- Else we let go of this step, for heading for the next.

Once we know that there will soon be a price change of over 3% in 5 hours with confidence of 95%, for example, then we may buy the asset immediately, so without incurring the decision cost, in the hope of selling them back at a higher price. If the confidence is 65% only, then we want to spend decision cost to be sure of the coming price rise.

**What is the status of traditional indicators?**

Traders have a wide range of technical analysis tools and trading indicators. An indicator is a function of historical prices, volumes, order book states. Although a compound indicator has, as its input, the values of other indicators, they also fall in to the same category as simple indicators.

All the indicators are only valuable to the extent to which they contribute to the prediction of price trending, no matter how smart, complex, or sophisticated they are.

An indicator can be either an AI indicator or a traditional indicator. While an AI indicator is mostly likely in the form of a Deep Neural Network with hundreds of millions of computed parameters inside it, a traditional indicator is a human-readable, manually-written analytical expression. Both of them are a function of prices and volumes. The human-readability itself of an indicator is not important.

Looking into the practice of using traditional indicators, we find that they lack quantitative optimization. Back-testing itself does not optimize an indicator/strategy, but helps choose passable or better ones from a handful of candidates. What finally distinguishes AI indicators from traditional ones, is that an AI indicator is the best of huge number of arbitrary (to a good extent, of course) functions, while a traditional indicator is the best of a handful of human-invented functions.

Imagine that there exists an ideal indicator that we ever want to find. It is clear that the ideal indicator is not exactly one of the 100+ human-invented functions. 

Which of arbitrary functions and human-invented indicators, can approach closer to the ideal indicator? Arbitrary functions! 

Then, which one can act as a better indicator? Is it an AI indicator, which is the best of arbitrary functions, or a traditional indicator, which is the best of human-invented functions? An AI indicator!

Although modern AI and Machine Learning technologies; like Transformer, GAN, and their variants; don't directly apply to automatic trading, they have huge potential in market games. Traditional indicators will eventually become almost obsolete in this age of modern AI, although they can be used as an auxiliary input to AI indicators as a shortcut input to AI models.

This project aims to achieve a significant performance gain of automatic trading bot by exploring and exploiting the potential of modern AI technologies. We will tap into the true fundamentals of cutting-edge Machine Learning. The goal, therefore, is building a simply structured trading bot yet with rich AI indicators, rather than a full trading bot with a complete range of functionalities. AI is the focus of this project.

As a data scientist with some years of experience in trading and trading strategies, I am sure that if indicators based on modern AI do not work, neither do all traditional indicators. So, if this project, or AI indicators, ever fail then traditional indicators will have failed earlier.
