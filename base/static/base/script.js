let html = document.querySelector("html");

if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    // user prefers dark color scheme
    html.setAttribute("data-bs-theme", "dark")
}

else {
    // user prefers light color scheme
    html.setAttribute("data-bs-theme", "light")
}

if (window.location.pathname === '/history/') {
    document.addEventListener('DOMContentLoaded', function(event) {
        let txnBtn = document.querySelector("#txn-btn");
        let trfBtn = document.querySelector("#trf-btn");
        let txn = document.querySelector("#txn");
        let trf = document.querySelector("#trf");

        trfBtn.addEventListener('change', function(event) {
            txn.style.display = 'none';
            trf.style.display = 'block';
        })

        txnBtn.addEventListener('change', function(event) {
            txn.style.display = 'block';
            trf.style.display = 'none';
        })
    })
    
}

currLocation = window.location.pathname
if (currLocation === '/' || currLocation === '/history/' || currLocation.includes('/search/') ) {
    document.addEventListener('DOMContentLoaded', function(event) {
        document.querySelectorAll('.delete-button').forEach(item => {
            item.addEventListener('click', event => {
                const transactionId = item.dataset.transactionId;
                console.log(transactionId)
                
                form = document.querySelector('form#deleteTransactionForm')
                form.action = "/delete/" + transactionId + "/"
                console.log(form)
            });
        });
    })
    
}

