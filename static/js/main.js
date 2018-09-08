$(document).ready(function() {


    $(".tag").on("click",function () {
        if($(this).hasClass("Betrieb")){
            $(this).removeClass("Betrieb");
            $(this).addClass("Urlaub");
            url_d = parseInt($("#left_vac").text()) - 1;
            $("#left_vac").text(url_d);
            addEntry(this);
            //$(this).css("background-color","orange");
        }
        else if($(this).hasClass("Urlaub")){
            $(this).removeClass("Urlaub");
            $(this).addClass("Gleittag");
            url_d = parseInt($("#left_vac").text()) + 1;
            $("#left_vac").text(url_d);
            gleit_d = parseInt($("#gleit_count").text()) + 1;
            $("#gleit_count").text(gleit_d);
            $(this).innerHTML += " Urlaub";
            addEntry(this);
        }
        else if($(this).hasClass("Gleittag")){
            gleit_d = parseInt($("#gleit_count").text()) - 1;
            $("#gleit_count").text(gleit_d);
            ill_d = parseInt($("#illness_count").text()) + 1;
            $("#illness_count").text(ill_d);
            $(this).removeClass("Gleittag");
            $(this).addClass("Krankheit");
            addEntry(this);
        }
        else if($(this).hasClass("Krankheit")){
            ill_d = parseInt($("#illness_count").text()) - 1;
            $("#illness_count").text(ill_d);
            $(this).removeClass("Krankheit");
            $(this).addClass("Berufsschule");
            addEntry(this);
        }
        else if($(this).hasClass("Berufsschule")){
            $(this).removeClass("Berufsschule");
            $(this).addClass("Betrieb");
            addEntry(this);
        }
    });
});


function addEntry(that){
    console.log($(that).attr('id'));
    console.log($(that).attr('class').split(' ').pop());

    entry = {
        date: $(that).attr('id'),
        category: $(that).attr('class').split(' ').pop()
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