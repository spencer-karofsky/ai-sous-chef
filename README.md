# AI Sous Chef

### Description

**A hands-free, low-cost kitchen assistant powered by AWS and on-device interaction.**

AI Sous Chef turns cooking into a frictionless experience.

Instead of scrolling through recipe sites, ads, and infinite paragraphs, you simply ask what you want to make—“I want pasta,” “something with chicken,” “a 20-minute dinner”—and the device instantly returns clean, structured recipes.

Built with a custom ETL pipeline, a keyword-search engine, and a minimal AWS architecture (Lambda + S3 + API Gateway), the system delivers fast, zero-cost lookups to a dedicated Raspberry-Pi-based kitchen tablet.

The motivation is simple:
Cooking shouldn’t require a phone, a search engine, or patience. Just ask, and cook.


### AWS Disclaimer

Amazon Web Services is an integral component of this project, so I write Infrastructure as Code (IaC) to provision and tear down almost all AWS services programatically. However, some actions (such as creating an access key) must be completed first in the console; re-creating this project requires a baseline understanding of AWS.