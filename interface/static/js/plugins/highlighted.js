Vue.component('highlight-view', {
    template:`<div class='line-view file-style'>
            <ul :class='["lines", {empty: lines.length==0}]' ref='lineView'>
                <li v-for='(line, key) in lines' class='line'>
                    <div class='line-index'>
                        <span class='number'>{{ key + 1 }}</span>
                    </div>
                    <div v-html='line' class='line-value'></div>
                </li>
            </ul>
        </div>`
    , data(){
        return {
            lines: ['highlight-view']
        }
    }
})



class HighlightFile {

    constructor(){

    }

    points(){
        return {
            'file-view': 'highlight-view'
        }
    }

    template(){
        return `HighlightFile view`
    }

    init(plugins){
        bus.$on('file-content', this.fileContent.bind(this))
        bus.$on('file-highlight', this.fileHighlight.bind(this))
        this.worker = new Worker('/static/js/render-worker.js');
        let style = '<style type="text/css">#file_view .content { display: none !important; }; .line-view { background: rgb(250, 250, 250);}</style>'
        document.getElementsByTagName('head')[0].innerHTML += style
    }

    fileContent(d){
        console.log('HighlightFile')
        let parent = pluginPlaces['file-view'].$refs.highlight[0]
        // parent = d.parent
        this.renderCodeView(parent, d.content)
    }

    fileHighlight(d){
        this.el.lines = d
        //this.el.innerHTML = d.join('\n')
    }

    renderCodeView(el, code) {
        this.el = el 
        this.worker.onmessage = function(event) { 
            console.log('returned data')
            bus.$emit('file-highlight', event.data); 
        }

        this.worker.onerror = function(event) { 
            console.log('error', event)
        }

        this.worker.postMessage(code);
    }
}



register({
    name: 'highlight'
    , init(plugins) {
        // return this;
        return new HighlightFile
    }

    , mounted(plugin, plugins) {
        
        plugin.init(plugins)

    }
})