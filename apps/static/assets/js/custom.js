codeInput.registerTemplate("syntax-highlighted", codeInput.templates.prism(Prism, []));

function showModal(title, response){
    $("#modal-title").text(title);
    let messages = "";
    if (typeof response === "string") {
        messages = response;
    } else {
        for (let key in response) {
            messages += response[key] + "\n";
        }
    }
    $("#modal-body-text").text(messages);
    $("#modal-upload").modal("show");
}