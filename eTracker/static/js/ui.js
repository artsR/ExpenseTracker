// Toggle current Nav Menu option active:
document.addEventListener('DOMContentLoaded', checkActiveMenu)

// Adapt Menu to collapse and expand (responsiveness):
const active = document.getElementById('navbar')
const sidemenu = document.querySelector('aside div.sidemenu')

active.addEventListener('click', makeActive)
if(sidemenu) {
    sidemenu.addEventListener('click', makeActive)
}

function makeActive(e) {
    var toSwitch = e.target
    var navbar = document.getElementById('navbar')

    if (navbar.classList.contains('active')) {
        navbar.classList.toggle('active')
    } else if (toSwitch.classList.contains('toggle')) {
        navbar.classList.toggle('active')
    } else if (toSwitch.classList.contains('sidemenu')) {
        toSwitch.classList.toggle('active')
    }
}

function checkActiveMenu() {
    const path = window.location.pathname;
    const optionsMenu = document.querySelectorAll('nav > ul > li')

    optionsMenu.forEach(option => {
        var href = option.lastChild.getAttribute('href')
        if (path.substring(0, href.length) === href) {
            option.classList.add('active')
        }
    })
}

// Insert wallet Details:
function walletDetails(e, subwallet, currency) {
    // Provides list of subwallets for chosen Wallet:
    var subwalletField = document.getElementById(subwallet);
    var currencyField = document.getElementById(currency);
    var walletID = e.target.value;

    fetch(`/wallets/${walletID}`)
    .then(res => res.json())
    .then(data => {
        var optionHTML = '';
        for(let subwallet of data.subwallets) {
            optionHTML += `
                <option value="${subwallet.id}">${subwallet.name}</option>
            `;
        }
        subwalletField.innerHTML = optionHTML;
        currencyField.innerText = data.currency.abbr;
    });
};
