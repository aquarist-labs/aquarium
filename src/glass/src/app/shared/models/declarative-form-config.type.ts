export type FormFieldConfig = {
  name: string;
  type: 'text' | 'password';
  label?: string;
  value?: any;
  readonly?: boolean;
  required?: boolean;
  hint?: string;
  class?: string;

  // text | password
  hasCopyToClipboardButton?: boolean;
};

export type DeclarativeFormConfig = {
  fields: FormFieldConfig[];
};
