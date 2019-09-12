var last_tag_clicked = null;
$(document).ready(function() {


    $(".tag").on("click",function () {
        if (last_tag_clicked != null){
            $(last_tag_clicked).css("background-color","white");
        }
        last_tag_clicked = this;
        $(this).css("background-color","yellow");
    });
});


function addEntry(that){

    entry = {
        date: $(that).attr('id'),
        category: $(that).attr('class').split(' ').pop(),
        year: document.getElementById('jahreszahl').innerHTML

    };
    console.log(entry);
    $.ajax({
        type: "POST",
        url: "/postEntry",
        data: JSON.stringify(entry, null, '\t'),
        contentType: 'application/json;charset=UTF-8',

        succes: function (result) {
            //window.location.href ='/';
        }
    })
}

function addCat(){

    cat = {
        category: $('#cat_name').val(),
        value: $('#cat_value').val(),
        color: $('#cat_color').val()

    };
    $.ajax({
        type: "POST",
        url: "/addCat",
        data: JSON.stringify(cat, null, '\t'),
        contentType: 'application/json;charset=UTF-8',

        succes: function (result) {
            //window.location.href ='/';
        }
    })
}

$(document).ready(function () {
            for (i = 0; i < entries.length; i++) {
                tring = "#" + entries[i].id;
                $(tring).removeClass($(tring).attr('class').split(' ').pop());
                $(tring).addClass(entries[i].category);
            }
            keys = Object.keys(cat);
            console.log(cat["Urlaub"]);
            cat_infos = "";
            for ( i = 0; i < keys.length; i++){
                cat_info = "<div class='info_cat' id='" + keys[i] + "_info' style='background-color: "+ cat[keys[i]][1]+"'>" + keys[i]+ " " +
                    cat[keys[i]][0] + "</div>";
                cat_infos += cat_info;
            }
            $("#cat_info").append(cat_infos);

        });