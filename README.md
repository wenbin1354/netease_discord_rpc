# Netease Discord RPC

# Update to show song cover

Replace cookies with you own cookies in `config.py`


```bash
function getCookiesAsJson() {
    const cookies = document.cookie.split('; ');
    const cookieJson = {};

    cookies.forEach(cookie => {
        const [name, value] = cookie.split('=');
        cookieJson[name] = value;
    });

    return cookieJson;
}
const cookieJson = getCookiesAsJson();
console.log(JSON.stringify(cookieJson, null, 4));
```


### To bundle the script

```python
pyinstaller --onefile main.py
```