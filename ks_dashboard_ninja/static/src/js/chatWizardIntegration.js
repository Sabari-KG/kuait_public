/** @odoo-module **/

import { chatWizard } from '@ks_dashboard_ninja/js/chatWizard';
import { Ksdashboardgraph } from '@ks_dashboard_ninja/components/ks_dashboard_graphs/ks_dashboard_graphs';
import { Ksdashboardtodo } from '@ks_dashboard_ninja/components/ks_dashboard_to_do_item/ks_dashboard_to_do';
import { Ksdashboardtile } from '@ks_dashboard_ninja/components/ks_dashboard_tile_view/ks_dashboard_tile';
import { patch } from "@web/core/utils/patch";
import { Ksdashboardkpiview } from '@ks_dashboard_ninja/components/ks_dashboard_kpi_view/ks_dashboard_kpi';

patch(Ksdashboardgraph.prototype,{

    _openChatWizard(ev){
        ev.stopPropagation();
        this.env.services.dialog.add(chatWizard,{
            itemId: this.item.id,
            dashboardId: this.ks_dashboard_data.ks_dashboard_id,
            dashboardName: this.ks_dashboard_data.name,
            itemName: this.item.name
        })
    }
});

patch(Ksdashboardkpiview.prototype,{

    _openChatWizard(ev){
        ev.stopPropagation();
        this.env.services.dialog.add(chatWizard,{
            itemId: this.item.id,
            dashboardId: this.ks_dashboard_data.ks_dashboard_id,
            dashboardName: this.ks_dashboard_data.name,
            itemName: this.item.name
        })
    }
});


patch(Ksdashboardtodo.prototype,{

    _openChatWizard(ev){
        ev.stopPropagation();
        this.env.services.dialog.add(chatWizard,{
            itemId: this.item.id,
            dashboardId: this.ks_dashboard_data.ks_dashboard_id,
            dashboardName: this.ks_dashboard_data.name,
            itemName: this.item.name
        })
    }
});

patch(Ksdashboardtile.prototype,{

    _openChatWizard(ev){
        ev.stopPropagation();
        this.env.services.dialog.add(chatWizard,{
            itemId: this.item.id,
            dashboardId: this.ks_dashboard_data.ks_dashboard_id,
            dashboardName: this.ks_dashboard_data.name,
            itemName: this.item.name
        })
    }
});

