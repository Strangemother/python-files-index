var folderField = Vue.component('form-field', {
    //el: "#folder_field"
    template: `<div id="folder_field" :class="['status-' + status, {valid: valid == true, invalid: valid == false, untested: valid == undefined}]">
            <div class="input-field col s12">
                <input
                    id="folder_path"
                    type="text"
                    v-model='folderPath'
                    v-on:keyup.13="submit"
                    list='folder_list'
                    v-on:keyup="keyup"
                    class="validate">
                <label for="folder_path">Folder path</label>
            </div>

            <datalist id='folder_list'>
                <option v-for='folder in subFolders' :value='folder'></option>
            </datalist>

            <div :class="[{hidden: selected != undefined || folderPath.length < 3}, 'status-view', status]">{{ status }}

                <div :class="['flow-panel good', { show: existing == true }]">
                    <h3>Looks Good!</h3>
                    <p>That's a valid folder with an existing <span class="code">.git</span> folder. We'll pick up from its last point.</p>

                    <div class="actions">
                        <button class="btn" @click='select()'>Pick it</button>
                    </div>

                </div>

                <div :class="['flow-panel bad file-panel', { show: isfile == true }]">
                    <h3>A File?</h3>

                    <p>The given path <span class="code">{{ basename }}</span> has a file extension.
                        <span class="text-warning">A directory is expected.</span>
                     </p>

                     <div :class="['goto-root-question', { show: result.in_previous == true}]">
                         <p class="question">Did you mean the directory: <span class="code">{{ result.backward_dir }}</span> (it contains a <span class="code">.git</span> folder)?</p>

                        <div class="actions">
                            <button class="btn" @click='select(result.backward_dir)'>Use Suggested</button>
                        </div>
                     </div>
                </div>

                <div :class="['flow-panel bad', { show: valid && result.in_previous == true && !isfile }]">
                    <h3>Sub Folder?</h3>

                    <p class='text-warning'>This directory is not the root of a found <span class="code">.git</span> project but the parent directory <span class="code">{{ result.backward_dir }}</span> does contain a <span class="code">.git</span> repository. </p>

                    <p class='question'>Would you like to change this to <span class="code">{{ result.backward_dir }}</span>?</p>

                    <div class="actions">
                        <button class="btn" @click='select(result.backward_dir)'>Yes</button>
                        <button class="btn" @click='select()'>No, create a submodule</button>
                    </div>

                </div>

                <div :class="['flow-panel bad', { show: folderPath.length> 0 && !valid && !existing && !isfile }]">
                    <h3>New Folder?</h3>

                    <p><span class="text-warning">This directory doesn't exist</span>, but you can create a new folder called "<span class="code">{{ basename }}/</span>" with a new <span class="code">.git</span> repository. Any existing data is safe.</p>

                    <p class="question">Would you like to create a new folder called <span class="code">{{ basename }}/</span>?</p>

                    <div class="actions">
                        <button class="btn" @click='select()'>Create Folder</button>
                    </div>

                </div>

                <div :class="['flow-panel bad', { show: folderPath.length > 0 && valid && !existing && !isfile && !result.in_previous }]">
                    <h3>Create Here?</h3>

                    <p><span class="warning">This directory is not a <span class="code">git</span> repository</span> so a new one will be created. Any existing data is safe.</p>

                    <p class="question">Would you like to create a respository in this folder?</p>

                    <div class="actions">
                        <button class="btn" @click='select()'>Create Repo</button>
                    </div>

                </div>

            </div>
            <div :class="[{hidden: selected == undefined}, 'selected-view']">
                <h2>Confirm</h2>
                <p>Great! A git repo is bound for: <span class="code">{{ selected }}</span></p>
                <div class="actions">
                    <button class="btn right" @click='selected=undefined'>Change</button>
                    <button class="btn" @click='complete()'>Continue</button>
                </div>
            </div>
        </div>
    `

    , data(){
        return {

            folderPath: ''
            , subFolders: []
            , status: 'unused'
            , valid: undefined
            , existing: undefined
            , basename: ''
            , isfile: false
            , isdir: undefined
            , result: {}
            , selected: undefined
        }
    }

    , mounted(){

    }

    , methods: {

        submit(){
            /* User pressed enter on the field. Perform a check and continue if
            valid. */
            this.status = 'checking'
            // Submit check to JSON
            // render wait.
            serverPost('/valid/folder/', {
                path: this.folderPath
            }, this.validFolderHandler.bind(this))
        }

        , select(path) {
            this.selected = path || this.folderPath
            console.log('selected', this.selected)
        }

        , complete(){
            this.folderPath = this.selected
            bus.$emit('folderPath', { selected: this.selected })
        }

        , keyup(e) {

            if(this.folderPath == this.checkedPath) {
                return
            }

            if(this.lastCall != undefined) {
                this.lastCall.abort()
            }

            this.checkedPath = this.folderPath
            this.lastCall = serverPost('/sub-folders/', {
                path: this.folderPath
                , forgiving: true
            }, this.keyupCallback.bind(this))

            this._autoKeep = this.folderPath
            if(this.autoCall != undefined) {
                clearTimeout(this.autoCall)
            }

            this.autoCall = setTimeout(function(){
                if(this._autoKeep == this.folderPath) {
                    this.submit()
                    delete this._autoKeep
                }
            }.bind(this), 1000)
        }

        , keyupCallback(d) {
            /* result from the server call, containing a list of next folders.*/
            this.lastCall = undefined
            // whipe
            this.subFolders.splice(0, this.subFolders.length)
            for(let f of d) {
                this.subFolders.push(f)
            }
            // replace subfolders

        }

        , validFolderHandler(data) {
            this.valid = data.valid
            this.status = 'done'
            console.log(data)
            this.result = data
            this.existing = data.existing
            this.basename = data.basename
            this.isfile = data.isfile
            this.isdir = data.isdir
        }
    }
})

