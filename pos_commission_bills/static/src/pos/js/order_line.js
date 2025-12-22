import {PosOrderline} from "@point_of_sale/app/models/pos_order_line";
import {Orderline} from "@point_of_sale/app/generic_components/orderline/orderline";
import {patch} from "@web/core/utils/patch";


patch(PosOrderline.prototype, {
    setup(vals) {
        this.commission_rate = this.product_id.commission_rate ?? 0;
        this.storage_fees = this.product_id.storage_fees ?? 0;
        return super.setup(...arguments);
    },
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            commission_rate: this.commission_rate ?? this.get_product().commission_rate ?? 0,
            storage_fees: this.storage_fees ?? this.get_product().storage_fees ?? 0,
        };
    },

    setLineCommissions(value) {
        const parsed_commission = !isNaN(value)
            ? value
            : isNaN(parseFloat(value))
                ? 0
                : parseFloat("" + value);
        this.commission_rate = parseFloat(parsed_commission) || 0.0;
        this.setDirty();
    },
});

patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            ...Orderline.props.line,
            shape: {
                ...Orderline.props.line.shape,
                commission_rate: Number,
                storage_fees:Number,
            },
        },
        is_report: { type: Boolean, optional: true },
    },
    defaultProps: {
        ...Orderline.defaultProps,
        is_report: false,
    },
});
