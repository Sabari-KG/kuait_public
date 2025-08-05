/** @odoo-module **/

import { LoadingIndicator } from "@web/webclient/loading_indicator/loading_indicator";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { useService } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";
import { useEffect, useRef, xml } from "@odoo/owl";


patch(LoadingIndicator.prototype, {
  setup() {
    super.setup();
  },
      requestCall({ detail }) {
        if (detail.settings.silent) {
            return;
        }
        if (this.state.count === 0) {
            browser.clearTimeout(this.startShowTimer);
            this.startShowTimer = browser.setTimeout(() => {
                if (this.state.count) {
                    this.state.show = true;
                    let ks_active_el = $(this.env.services.ui.activeElement).find('.chat-ai-box').length
                    if((!ks_active_el) &&( this.env.services.action.currentController?.action?.tag === 'dashboard_ninja'
                                        || this.env.services.action.currentController?.action?.tag === 'ks_dashboard_ninja'
                                        || this.env.services.action.currentController?.action?.xml_id === 'ks_dashboard_ninja.layout_tree_action_window'
                                        || this.env.services.action.currentController?.action?.xml_id === 'ks_dashboard_ninja.board_form_tree_action_window')){
                        this.blockUITimer = browser.setTimeout(() => {
                                this.shouldUnblock = true;
                                this.uiService.block();
                            }, 3000);
                    }
                }
            }, 250);
        }
        this.rpcIds.add(detail.data.id);
        this.state.count++;
    },

});

patch(BlockUI.prototype, {
    setup(){
        super.setup();
        this.menuService = useService('menu');
        this.loaderImg = useRef('loaderImg');

        useEffect( () => {
            if(this.loaderImg && this.loaderImg.el && this.loaderImg.el.src){
                this.loaderImg.el.src = "/web/static/img/spin.svg"
            }
            let currentApp = this.menuService?.getCurrentApp();
            if (currentApp && currentApp.xmlid === "ks_dashboard_ninja.board_menu_root"){
                if(this.loaderImg && this.loaderImg.el && this.loaderImg.el.src){
                    this.loaderImg.el.src = "/ks_dashboard_ninja/static/images/loader.gif"
                }
            }
        });
    }
})

BlockUI.template = xml`
    <div t-att-class="state.blockUI ? 'o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100' : ''" >
      <t t-if="state.blockUI">
        <div class="o_spinner mb-4">
            <img src="/web/static/img/spin.svg" alt="Loading..." t-ref="loaderImg"/>
        </div>
        <div class="o_message text-center px-4">
            <t t-esc="state.line1"/> <br/>
            <t t-esc="state.line2"/>
        </div>
      </t>
    </div>`;

