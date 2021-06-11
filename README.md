# AI-Trading-Bot
Automatic Trading Bot based on AI-based indicators.

Is it time to enter a position?

While both of them are the core questions for an automatic trading bot, "Is it time to enter a position?" is more important than "Is it time to exit the position?", as exiting a position has two obvious scenarios: Take Profit and Stop Loss. Entering a position, however, requires your confidence that the position will have chance to be existed with profit in the near future.

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
- % means the percentage of the referred amount over the original quote quantity that was possessed before entering,
- total price change is the price difference between the start of up-trending before entering and the start of down-trending before exiting,
- decision cost is the price change monitored/consumed, after the starts of trending, to finally decide on entering and exiting,
- price slippage is the price difference between the buy/sell order and its actual fulfilling transaction,
- and exchange fees are the fees paid to the exchange on buying and selling,

Total price change (TPC) is the only variable that should be predicted before deciding on entering a position.

An example is

Net Profit
= (%TPC - 0.07% x 2 – 0.1% x 2 - 0.5% x 2) X (original 5,000 USDT)
= (%TPC - 1.34% ) x 5,000 USDT,

where they are all multiplied by 2 because there are two exchange actions: enter and exit.

So, the least indicator that we need should answer the question "Will be there a price change of over 1.34%, in the near future?" or, in general,

"Will be there a price change of over X% within Y time period?", 

where X and Y should be optimized for an aimed performance.

Examples are: There will be a price change of over 50% in 10 months, 3% in 48 hours, 3% in 6 hours, and 2% in 3 hours, each with a certain confidence. It is better to shorten the time frame, because it is riskier to have longer time frame in technical analysis. These steep price changes are observed quite often in the crypto space.

Once we know that there will be a price change of over 3% in 5 hours with confidence of 80%, for example, then we decide to buy the asset immediately in the hope of selling them back at a higher price. Selling decision, however, is easier, because we will just sell when it is time to take profit or stop loss.

All the seemingly beautiful traditional indicators are only valuable to the extent to which they contribute to this type of prediction.
Looking at traditional indicators, in technical analysis, they are all a function of historical prices/volumes/order book states. No matter how smart, natural, intuitive, complex, or sophisticated those indicators are, they are at most 100+ individual functions of historical prices, volumes, and order book states. The smart quantitative logic and intuition themselves are worthless unless they contribute to prediction accuracy.

That said, why should we keep sticking to a handful of traditional indicators, while a simple Deep Neural Network alone can learn, or discover, a (proximation of the) profit-maximizing indicator from billions of candidates, which themselves are, and can approximate, any continuous function of historical price, including the true indicator that we ever want to discover.

In a word, a DNN, when properly designed, can learn a proximation of ideal indicator, from observations of price change. There are unlimited observations of price change. Let's call the proximation of ideal indicator learnt by a DNN, the AI indicator, compared to traditional ones. Although modern AI and Machine Learning technologies; like Transformer, GAN, and their variants; don't directly apply to automatic trading, they have huge potential in market games.
Traditional indicators will eventually become almost obsolete in this age of modern AI, although they can be used as an auxiliary input to AI indicators, in addition to price/volume/order book state.

This project aims to achieve a significant performance gain of automatic trading bot by exploring and exploiting the potential of modern AI technologies. We will tap into the true fundamentals of cutting-edge Machine Learning. The goal, therefore, is building a simply structured trading bot yet with rich AI indicators, rather than a full trading bot with a complete range of functionalities. AI is the focus of this project.

As a data scientist with years of experience in trading and trading strategies, I am sure that if indicators based on modern AI do not work, neither do all traditional indicators. So, if this project, or AI indicators, ever fail then traditional indicators will have failed earlier.
