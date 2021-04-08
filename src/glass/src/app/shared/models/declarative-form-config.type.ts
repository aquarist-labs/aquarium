export type FormFieldConfig = {
  name: string;
  type: 'text' | 'password';
  label?: string;
  value?: any;
  readonly?: boolean;
  required?: boolean;
  hint?: string;

  // text | password
  hasCopyToClipboardButton?: boolean;
};

export type DeclarativeFormConfig = {
  title: string;
  subtitle?: string;
  fields: FormFieldConfig[];
  okButtonVisible?: boolean; // Defaults to `true`
  okButtonText?: string; // Defaults to `OK`
  okButtonResult?: any; // Defaults to form values
  okButtonClass?: string;
  cancelButtonVisible?: boolean; // Defaults to `true`
  cancelButtonText?: string; // Defaults to `Cancel`
  cancelButtonResult?: any; // Defaults to `false`
  cancelButtonClass?: string;
};
