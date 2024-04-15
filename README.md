# Welcome to DataWolt :yum:

* Datawolt is a Streamlit app that visualizes your food delivery data.
* To get started, you first need to install the [Datawolt chrome extension](https://chromewebstore.google.com/).
* Once you have the extension installed you can visit the [Wolt order history screen](https://wolt.com/me/order-history).
* The extension will automatically pull your order history, display an alert when it's done and forward your browser to your personal dashboard.
* Sample dashboard can be viewed [here](https://datawolt.streamlit.app/?userid=example).

#### Privacy and security
* Datawolt is **completely open-source** and the entire codebase can be viewed on [GitHub](https://github.com/idoavrah/datawolt).
* Datawolt **does not store** any of your identifiable personal data.
* Datawolt uses your temporary credentials to pull your order data from Wolt but saves only the relevant parts (orders, items, prices and restaurant names and locations). UserId is hashed, credentials are not saved anywhere.
* Your dashboard has a public endpoint and can be viewed by others if they know your hash-generated userid. The generated userid is basically impossible to guess and can not be traced back to the original Wolt userid or your username / e-mail.

![](./streamlit/demo.webm "Demo")
