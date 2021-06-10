# AI-Trading-Bot
Automatic Trading Bot based on AI-based indicators.

Is it time to enter a position?

While they are the core questions for an automatic trading bot, “Is it time to enter a position?” is much more important than “Is it time to exit the position?”, as exiting a position has two obvious scenarios: Take Profit and Stop Loss. Entering a position, however, requires your confidence that the position will have chance to be existed with profit in the near future. We know that 

Net Profit for a round of enter/exit = 
( % price change - % price slippage - % exchange fees ) x Quantity Traded for the round

, where we should predict the the percentage of price change before entering a position.

An example is 
Net Profit = (% price change - 0.07% x 2 - 0.1% x 2) x (30 ETH x ETH/USD price)
= ( % price change - 0.34% ) x (30 x $2,500)
, where they are multiplied with 2 due to two swaps: enter and exit.

So, the least indicator we need should answer the question “Will be there a price change of over 0.34%, in the near future?” or, in general, “Will be there a price change of over X% within Y time period?”, where X and Y should be optimized for an aimed performance.

Examples are: There will be a price change of over 50% in 10 months, 3% in 48 hours, 3% in 6 hours, 2% in 3 hours, and 1% in 2 hours, each with a certain confidence.

Once we know that there will be a price change of over 3% in 5 hours with confidence of 80%, then we decide to buy the asset right now in the hope of selling them at 3% higher price. Selling decision, however, is easier, because we will just sell when it’s time to take profit or stop loss.

All the seemingly beautiful traditional indicators should only work for this type of prediction.

Looking at traditional indicators, in technical analysis, they are all a function of historical prices. No matter how smart, natural, intuitive, complex, or sophisticated those indicators are, they are just at most 100+ individual functions of historical prices, volumes, and order book states. The smart quantitative logic and intuition itself are worthless unless they contribute to the prediction accuracy.

That said, why should we keep sticking to a handful of traditional indicators, while a simple Deep Neural Network alone can find a best function among billions of candidate functions, which can approximate any continuous function of historical price, including the hidden true, almighty, indicator that we imagine. Although modern AI and Machine Learning technolgies; like Transformer, Embedding, other NLP techniques, LSTM/GRU, GAN, and VAE-GAN; don't directly apply to automatic trading, you feel they have huge potential in market games.

Traditional indicators will eventually become almost obsolete in this age of modern AI, although they can be used as an auxilliary input to AI indicators, in addition to  price/volume/order book state.

This project aims to achieve a significant performance gain of automatic trading bot by exploring the potential of modern AI technologies.

The goal, therefore, is not building a full trading bot with a wide range of functionalities but a simply structured trading bot with rich AI indicators. AI is the focus of this project.

As a data scientist with years of experince in trading and trading strategies, I am sure that IF indicators based on modern AI do not work, THEN all traditional indicators also do not work. So, if this project, or AI indicators, fail then traditional indicators will also have failed.

