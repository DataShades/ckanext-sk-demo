/**
 * TomSelect adapter.
 * https://tom-select.js.org/
 */
ckan.module("sk_demo-tom-select", function () {

  return {
    // any attribute with `data-module-` prefix transforms into camelized
    // option. `data-module-hello-world="1"` becomes `helloWorld: 1`. Case
    // transformation happens only after hyphen. This is used to pass nested
    // options. For example, `data-module-hello-world_bye-world` becomes
    // `helloWorld_byeWorld`. Then options are processed by
    // `this.sandbox.sk_demo.nestedOptions` and we receive
    // `{helloWorld: {byeWorld: ...}}`.
    options: {

    },

    initialize() {
      // stop execution if dependency is missing.
      if (typeof TomSelect === "undefined") {
        // reporting the source of the problem is always a good idea.
        console.error("[sk_demo-tom-select] TomSelect library is not loaded");
        return
      }

      // tom-select has a number of nested options. We are using
      // `nestedOptions` helper defined inside `sk_demo.js` to
      // convert flat options of CKAN JS module into nested object.
      const options = this.sandbox["sk_demo"].nestedOptions(this.options);

      // in this case there is no value in keeping the reference to the
      // widget. But if you are going to extend this module, sharing
      // information between methods through `this` is a good choice.
      this.widget = new TomSelect(this.el, options);
    }
  }
})
