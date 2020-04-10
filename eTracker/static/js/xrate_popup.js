// Display Popup with Exchange Rate for Balance:
var timer = null;
var xhr = null;

function displayXRate(e) {
    var balanceElement  = e.target.closest('ul')
    if(!balanceElement || e.target.tagName !== 'LI') {
        return null;
    }
    var amount = balanceElement.lastElementChild.firstChild.textContent;
    var currencyElement = balanceElement.lastElementChild;console.log(currencyElement);
    if(balanceElement.lastElementChild.tagName === 'DIV') {
        currencyElement = currencyElement.previousElementSibling
    }
    var currency = currencyElement.querySelector('span').innerText;

    timer = setTimeout(() => {
        timer = null;
        xhr = (
            fetch(`/tools/xrate_popup/${currency}/${amount}`)
            .then(response => response.text())
            .then(data => {
                xhr = null;
                $(balanceElement).popover({
                    trigger: 'manual',
                    html: true,
                    animation: false,
                    placement: 'top',
                    container: balanceElement,
                    title: `${amount} ${currency}`,
                    content: data,
                    sanitize: false
                }).popover('show');
            })
        )
    }, 500);
};

function closeXRate(e) {
    var balanceElement  = e.target.closest('ul');

    if(timer) {
        clearTimeout(timer);
        timer = null;
    }
    else if(xhr) {
        // TODO: xhr.abort() w/o jQuery.
    }
    else {
        $(balanceElement).popover('dispose');
    }
};
