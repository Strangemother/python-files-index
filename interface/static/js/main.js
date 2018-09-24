var serverPost = function(path, data, handler, errorHandler){
    var success = function(result){
        //console.log('handle', result)

        if(result.valid == false) {
            if(errorHandler == undefined) {
                return raiseError(result, errorHandler)
            }

            return errorHandler(result)
        }

        handler && handler(result)
    }

    var failHandler = function(result){
        if(errorHandler != undefined) {
            return errorHandler(result)
        }

        raiseError(result)
    }

    return $.post(path, data, success).fail(failHandler)
}

var bus = new Vue({})


var raiseError = function(result) {
    /* throw the given error to the user*/
    console.warn("Error from remote call")
    console.log(result)
}


var initMaterialize = function(){

    var elem = document.querySelector('.sidenav');
    var instance = M.Sidenav.init(elem, {});
    $(document).ready(function(){
        $('.sidenav').sidenav();
    });
}

;initMaterialize();

$.fn.textWidth = function(text, font) {
    if (!$.fn.textWidth.fakeEl) $.fn.textWidth.fakeEl = $('<span>').hide().appendTo(document.body);
    $.fn.textWidth.fakeEl.text(
        text || this.val() || this.text() || this.attr('placeholder')).css('font', font || this.css('font')
    );
    return $.fn.textWidth.fakeEl.width();
};

// let tSelector = ".header-project-selector input.project-title"

// $(tSelector).on('input', function() {
//     var inputWidth = $(this).textWidth();
//     $(this).css({
//         width: inputWidth
//     })
// }).trigger('input');




// var targetElem = $(tSelector);

// inputWidth(targetElem);
