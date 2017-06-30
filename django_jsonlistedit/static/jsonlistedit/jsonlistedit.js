/* JSONListEdit (C) 2017 Daniel Fairhead
 * MIT Licence.
 */
(function () {
    "use strict";

    // Temporary hack for quick dev:
    var default_templates = {
            "default": '<div class="handle">☰</div><label>Name: $$name</label>, <label>price <input name="price" value="$price" type="number"/></label>',
            "section": '$$name',
            "notes": '$$name'
        };

    var default_config = {
        debug: false,

        defaultvalues: {},

        templateFunction: quicktemplate,

        listElement: 'div',
        itemElement: 'div',

    };

    /////////////////////////////
    // Helper functions:
    //

    function shallowCombine() {
        /* shallow copy from multiple objects into one, and return it */
        var newobj = {},
            objid, i;
        for (objid=0;objid<arguments.length;objid++) {
            for (i in arguments[objid]) {
                if (arguments[objid].hasOwnProperty(i)) {
                    newobj[i] = arguments[objid][i];
                }
            }
        }
        return newobj;
    }

    function findParentBefore(current, stopat) {
        /* work your way up the DOM tree,
           until you find the node before (inside) stopat. */
        while (current.parentNode !== stopat) {
            current = current.parentNode;
            if (current === null) {
                return false;
            }
        }
        return current;
    }

    function quicktemplate(obj, listobject) {
        /* Quick Hacky template function, for generating 'rows' in the list.
         * $$<var> is replaced by an inputbox with that name, which pulls in the value from the object.
         * $var pulls in the value from that object.
         * */
        var str = listobject.config.templates[obj._type || 'default'],
            k;

        str = str.replace(/\$\$(\w*)/g, '<input name="$1" class="jsonlistauto">');

        return str;
    }

    ////////////
    // Rather than pull in the whole sortable.js (which is excellent, by the way)
    // here's just enough draggable/sortableness to get us by:

    var Sortable = function () { };

    Sortable.create = function (container_element, options) {
        var items = [];
        var dragged_item = null;
        var drop_index = null;

        container_element.addEventListener('dragstart', function (evt) {
            var item = findParentBefore(evt.target, container_element);

            if (!item) { return false; }

            items = container_element.children;

            for (var _counter=0; _counter<items.length; _counter++) {
                items[_counter].index = _counter;
                items[_counter].index_orig = _counter;
            }

            item.classList.add('moving');
            evt.dataTransfer.effectAllowed = 'move'; 
            evt.dataTransfer.dropEffect = 'move'; 
            evt.dataTransfer.setData('text/html', item.innerHTML);
            dragged_item = item;
            return false;

        }, false);

        container_element.addEventListener('dragover', function (evt) {
            var item = findParentBefore(evt.target, container_element);
            var before = null;

            evt.dataTransfer.dropEffect = 'move';

            if (!item) {return false;}

            var size = item.getBoundingClientRect();

            before = evt.clientY < ( size.top + ( size.height / 2));

            if (evt.preventDefault) {
                evt.preventDefault(); // Necessary. Allows us to drop.
            }

            if (item != dragged_item) {
                if (before) {
                    item.parentNode.insertBefore(dragged_item, items[item.index]);
                    drop_index = item.index;
                } else {
                    drop_index = item.index + 1;
                    if (item.index === items.length) {
                        item.parentNode.appendChild(dragged_item);
                    } else {
                        item.parentNode.insertBefore(dragged_item, items[item.index + 1]);
                    }
                }
            }
            items = container_element.children;

            for (var _counter=0; _counter<items.length; _counter++) {
                items[_counter].index = _counter;
            }

            return false;
        });

        container_element.addEventListener('dragend', function (evt) {
            var item = findParentBefore(evt.target, container_element);

            if (!item) {return false;}

            item.classList.remove('moving');
            if(dragged_item.index < drop_index) {
                drop_index--;
            }
            options.onEnd({ oldIndex: dragged_item.index_orig, newIndex: drop_index });

        })

    }

    ///////////////////////////////

    var JSONListEdit = function (textarea, config) {
        var that=this;
        this.textarea = textarea;
        this.config = shallowCombine(default_config, config);

        if (this.config.domNode) {
            this.el = this.config.domNode;
        } else {
            // Add our element / widget to the DOM:
            this.el = document.createElement(this.config.listElement);
            textarea.parentNode.insertBefore(this.el, textarea);
        }
        this.el.className += ' jsonlisteditor';

        this.UpdateConfigFromDataSet();
        this.LoadTextArea();
        this.CreateAllRows();
        this.connectButtons();

        if (this.config.debug !== true) {
            textarea.style.display = 'none';
        }

        Sortable.create(this.el, {
            "onEnd": function (evt) {
                var x = that.list.splice(evt.oldIndex, 1);
                that.list.splice(evt.newIndex, 0, x[0]);
                that.updateTextArea();
            },
            "handle": ".handle",
        });


        return this;
    }

    JSONListEdit.prototype.UpdateConfigFromDataSet = function () {
        for (var k in this.textarea.dataset) {
            this.config[k] = this.textarea.dataset[k];
        }
    }

    JSONListEdit.prototype.LoadTextArea = function () {
        try {
            this.data = JSON.parse(this.textarea.value);
            this.list = this.data[this.config.arrayname] || this.data;
        } catch (err) {
            this.el.innerHTML = '<div class="error">' + err + '</div>';
            this.data = {};
            this.list = [];
        }
    }

    JSONListEdit.prototype.AddDOMRow = function (obj, innerHTML) {
        var div = document.createElement(this.config.itemElement),
            mytype = obj._type || 'default',
            editor = this,
            inputs,
            i,
            myvalue;

        div.className = 'item ' + mytype;
        div.innerHTML = innerHTML;
        div.draggable = true;

        // Update the values of all input boxes to have the current value from the obj:

        inputs = div.querySelectorAll('.jsonlistauto');

        for (i=0;i<inputs.length;i++) {
            myvalue = obj[inputs[i].name];
            if (myvalue === undefined){
                if (editor.config.defaultvalues[mytype]) {
                    myvalue = editor.config.defaultvalues[mytype][inputs[i].name]
                }
            }
            if (myvalue === undefined) {
                myvalue = '';
            }

            inputs[i].value = myvalue;
        }

        // And whenever those values change in the DOM, update the obj:

        div.onchange = function (evt) {
            if (editor.config.onItemInputChange) {
                editor.config.onItemInputChange(evt, editor);
            }
            obj[evt.target.name] = evt.target.value;
            editor.updateTextArea();
        }

        // Make 'delete' buttons work:

        div.onclick = function (evt) {
            if (evt.target.classList.contains('deleteitem')) {
                editor.delete(obj, div)
            }
        }

        this.el.appendChild(div);
        return div; 
    }

    JSONListEdit.prototype.CreateAllRows = function () {
        // Add original elements from array into HTML list:

        for (var i=0;i<this.list.length;i++){
            this.AddDOMRow(this.list[i], this.config.templateFunction(this.list[i], this));
        }

    }

    JSONListEdit.prototype.updateTextArea = function () {
        /* Update the original textarea to have the current data. */
        this.textarea.value = JSON.stringify(this.data);
    }

    JSONListEdit.prototype.addItem = function (data) {
        this.list.push(data);
        this.updateTextArea();
        if (this.config.preAddItem) {
            data = this.config.preAddItem(data, this);
        }
        this.AddDOMRow(data, this.config.templateFunction(data, this));
        this.config.onAdd && this.config.onAdd(data, this);
    }

    JSONListEdit.prototype.delete = function (obj, rowdiv) {
        this.list.splice(this.list.indexOf(obj), 1);
        this.updateTextArea();
        this.el.removeChild(rowdiv);
    }

    JSONListEdit.prototype.connectButtons = function (buttonsdiv) {
        // All .additem classed buttons in the buttonsdiv will add a new
        // item to the list.  The 'data-item' property defines what should be added.
        var that=this;

        if (!buttonsdiv) {
            var divs = document.getElementsByClassName('jsonlistedit_buttons');
            for (var i=0; i<divs.length; i++) {
                if (divs[i].dataset['for'] === this.textarea.name) {
                    buttonsdiv = divs[i];
                    break;
                }
            }
        }
        if (buttonsdiv) {
            buttonsdiv.onclick = function (evt) {
                if (evt.target.classList.contains('additem')) {
                    that.addItem(JSON.parse(evt.target.dataset['item']));
                }
            }
        }
    };


    // Run only once Setup:

    (function () {
        // Add new 'NOSUBMIT' form, to attach fields to.
        var d = document.createElement('form'),
            s = document.getElementsByTagName('script')[0];
        d.name = 'NOSUBMIT';
        s.parentNode.appendChild(d, s);

        window.JSONListEdit = JSONListEdit;
    }());

})();
