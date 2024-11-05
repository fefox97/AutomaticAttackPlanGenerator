import { minimalEditor, basicEditor, fullEditor, readonlyEditor } from "prism-code-editor/setups"
// Importing Prism grammars
import "prism-code-editor/prism/languages/markup"

const editor = basicEditor(
  "#editor",
  {
    language: "html",
    theme: "github-dark",
  },
  () => console.log("ready"),
)

codeInput.registerTemplate("syntax-highlighted", codeInput.templates.prism(Prism, []));

function showModal(title, response, autohide = false, large = false){
    $("#modal-title").text(title);
    let messages = "";
    if (typeof response === "string") {
        messages = response;
    } else {
        for (let key in response) {
            messages += key + ": " + response[key] + "\n";
        }
    }
    $("#modal-body-text").text(messages);
    if (large) {
        $("#modal-upload").addClass("modal-lg");
    }
    $("#modal-upload").modal("show");
    if (autohide) {
        setTimeout(function() {
            $("#modal-upload").modal("hide");
        }, 2000);
    }
}

function showAlert(response, type, icon){
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>
                <span class="material-symbols-outlined">${icon}</span>
                <span>${response.message}</span>
            </div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>',
    ].join('')
    $('#liveAlertPlaceholder').append(wrapper)
    setTimeout(function() {
        wrapper.remove()
    }, 5000)
}

function enableTab() {
    var textareas = document.getElementsByTagName('textarea');
    var count = textareas.length;
    for(var i=0;i<count;i++){
        textareas[i].onkeydown = function(e){
            if(e.keyCode==9 || e.which==9){
                e.preventDefault();
                var s = this.selectionStart;
                this.value = this.value.substring(0,this.selectionStart) + "\t" + this.value.substring(this.selectionEnd);
                this.selectionEnd = s+1; 
            }
        }
    }
}

$(document).ready(function() {
    $('.nav-item.active').children('.multi-level.collapse').collapse('show');
    enableTab();
});