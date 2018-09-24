var localCache = {}

window.onpopstate = function(event) {
    // console.log("location: " + document.location + ", state: " + JSON.stringify(event.state));

    if(event.state == null) {
        console.log('No previous')
        return
    }
    app.serve(event.state.path, false)
};


var app = new Vue({
    el: "#main"
    , data: {
        items: [
            'first'

        ]
        , meta: [
            false
        ]
        , path: []
        , itemCount: 12
        , seconds: 1
        , is_file: false
    }

    , mounted(){
        this.serve()
    }

    , methods: {

        stepUp() {
            if(this.path == null) {
                console.log('No path to step up.')
                return false
            }
            this.serve(this.path.slice(0, -1).join('/'))
        }

        , stepServe(item) {
            let path = item

            if(this.files && this.files.path != null) {
                let rpath = ''
                if(this.path != null) {
                    rpath = this.path.join('/')
                }
                if(rpath.length > 0) {
                    path = `${rpath}/${item}`
                }
            }
            return this.serve(path)
        }

        , resetCache(){
            localCache = {}
        }

        , serve(path, pushUrl=true) {
            this.startTime = +(new Date)
            let render = (function(){
                let self = this.self
                    , path = this.path

                return function(d, addToCache=true){
                    self.endTime = +(new Date)

                    if(addToCache!=false){
                        localCache[path] = Object.assign({}, d)
                    }

                    self.itemCount = d.meta.length
                    self.files = d
                    self.is_file = d.is_file

                    if(pushUrl && path != undefined) {
                        window.history.pushState({ path }, path, '/' + path)
                    }

                    self.$nextTick(function(){
                        //Vue.set(this, 'items', d.keys)
                        Vue.set(this, 'path', d.parts)
                        Vue.set(this, 'meta', d.meta == null? []: d.meta)

                        if(d.meta == null) {
                            this.$nextTick(function(){
                                this.serveMeta(path)
                            }.bind(this))
                        }
                        this.seconds = this.endTime - this.startTime
                    }.bind(self))
                }

            }).bind({path, self: this})


            if(localCache[path] != undefined) {
                console.log('rendering from cache', path)
                render()(localCache[path], false)
            } else {
                serverPost('/files/', { path }, render())
            }

        }

        , serveMeta(path) {
            serverPost('/files-meta/', { path }, function(d){
                this.meta = d
                Vue.set(this, 'meta', d.meta)
            }.bind(this))
        }

        , servePathAt(index, path) {
            this.serve(path.slice(0, index+1).join('/'))
        }
    }
})
