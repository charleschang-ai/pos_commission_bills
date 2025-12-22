/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
// import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import {_t} from "@web/core/l10n/translation";

export class SaleOrderListController extends ListController {

    setup() {
        super.setup();
        this.action = useService("action");
    }

    async SaleOrderCreate() {
        try {
            let action = {
                name: _t('Vendor Bills'),
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                context: {
                    default_move_type: 'in_invoice',
                    search_default_in_invoice: 1,
                },
                domain: [['move_type', '=', 'in_invoice']],
            };
            this.action.doAction(action, {
                onClose: () => {
                    if (this.model && this.model.load) {
                        this.model.load();
                    }
                }
            });
            // const result = await this.rpc('/create/baison_sale_orders', {});
        } catch (error) {
            console.error("Error importing bills:", error);
        }
    }
}

registry.category("views").add("sale_order_create_button", {
    ...listView,
    Controller: SaleOrderListController,
    buttonTemplate: "pos_commission_bills.SaleOrder.ListView.Buttons",
});
