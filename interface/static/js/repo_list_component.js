
var repoListComponent = Vue.component('repo-list', {
    template: `<div class="repos">
        <ul class="collection repo-list">
            <li v-for='project in repos'
                class="collecton-item repo-list-item">

                <a href="javascript:;" @click='select(project)'>
                    <span class="project-name">{{ project.name }}</span>
                    <!-- <span class="path">{{ project.path }}</span> -->
                </a>
            </li>
        </ul>
    </div>
    `
    , data(){
        return {

            repos: CACHE['projects'] || []
        }
    }

    , mounted(){
        // populate with data
        bus.$on('created-project', this.onCreatedProject.bind(this))
    }

    , methods: {

        select(project) {
            /* Select the project for the presented view*/
            bus.$emit('select-project', project)
        }

        , onCreatedProject(data) {

            this.repos[data.name] = data
            this.$forceUpdate()
        }
    }
})
