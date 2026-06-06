function add() {
    var input = document.getElementById("todoInput");
    var list = document.getElementById("list");
    var text = input.value.trim();
    if (text === "") {
        return;
    }
    var item = document.createElement("li");
    item.textContent = text;
    list.appendChild(item);
    input.value = "";
    input.focus();
}
