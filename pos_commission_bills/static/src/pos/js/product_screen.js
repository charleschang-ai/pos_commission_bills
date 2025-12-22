import {ProductScreen} from "@point_of_sale/app/screens/product_screen/product_screen";
import {patch} from "@web/core/utils/patch";
import {_t} from "@web/core/l10n/translation";
import {
    BACKSPACE,
    Numpad,
    getButtons,
    DEFAULT_LAST_ROW,
} from "@point_of_sale/app/generic_components/numpad/numpad";

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },

    getNumpadButtons() {
        const colorClassMap = {
            [this.env.services.localization.decimalPoint]: "o_colorlist_item_color_transparent_6",
            Backspace: "o_colorlist_item_color_transparent_1",
            "-": "o_colorlist_item_color_transparent_3",
            // "comm": "o_colorlist_item_color_transparent_10",
        };

        return getButtons(DEFAULT_LAST_ROW, [
            {value: "quantity", text: _t("Qty")},
            {value: "discount", text: _t("%"), disabled: !this.pos.config.manual_discount},
            {
                value: "price",
                text: _t("Price"),
                disabled: !this.pos.cashierHasPriceControlRights(),
            },
            BACKSPACE,
            {value: "comm", text: _t("Comm")},
        ]).map((button) => ({
            ...button,
            class: `
                ${colorClassMap[button.value] || ""}
                ${this.pos.numpadMode === button.value ? "active" : ""}
                ${button.value === "quantity" ? "numpad-qty rounded-0 rounded-top mb-0" : ""}
                ${button.value === "price" ? "numpad-price rounded-0 rounded-bottom mt-0" : ""}
                ${
                button.value === "discount"
                    ? "numpad-discount my-0 rounded-0 border-top border-bottom"
                    : ""
            }
                ${button.value === "comm" ? "numpad-qty my-0 rounded-0 border-top border-bottom" : ""}
            `,
        }));
    },

    onNumpadClick(buttonValue) {
        if (["quantity", "discount", "price", "comm"].includes(buttonValue)) {
            this.numberBuffer.capture();
            this.numberBuffer.reset();
            this.pos.numpadMode = buttonValue;
            return;
        }
        this.numberBuffer.sendKey(buttonValue);
    },


});