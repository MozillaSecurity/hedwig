![Logo](https://github.com/posidron/posidron.github.io/raw/master/static/images/hedwig.png)

Hedwig is a commit monitor for GitHub using the GitHub REST API.


Create a hedwig.json file which contains your GitHub Token.
```
{
    "github": {
        "token": "<TOKEN>"
    }
}
```


```
python hedwig.py -project mozilla-inbound -repositories repositories.json -keywords keywords/debug.json
```
