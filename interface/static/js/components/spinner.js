var spinner = new Vue({
    el: '#spinner'
    , data: {
        loading: false
        , project: {}
    }
    , mounted(){
        bus.$on('select-project', function(project){
            this.project = project
        }.bind(this))
    }
    , methods: {
        spin() {
            this.loading = true
        }

        , stop(){
            this.loading = false;
        }

        , statusRefresh(){
            bus.$emit('select-project', this.project)
        }
    }
})

