export type FormFieldConfig = {
  name: string;
  type: 'text' | 'number' | 'password' | 'checkbox' | 'radio' | 'select';
  label?: string;
  value?: any;
  placeholder?: string;
  readonly?: boolean;
  autofocus?: boolean;
  hint?: string;
  groupClass?: string;
  validators?: {
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    required?: boolean;
    requiredIf?: Record<any, any>;
    pattern?: string | RegExp;
    patternType?: 'hostAddress';
  };
  onPaste?: (event: ClipboardEvent) => void;

  // text | password
  hasCopyToClipboardButton?: boolean;

  // dropdown
  options?: Record<any, string>;
};

export type FormButtonConfig = {
  type: 'default' | 'submit';
  text?: string;
  class?: string;
  click?: (buttonConfig: FormButtonConfig, values: Record<string, any>) => void;
};

export type DeclarativeFormConfig = {
  id?: string; // A unique form ID.
  hint?: string;
  subtitle?: string;
  fields: FormFieldConfig[];
  buttons?: Array<FormButtonConfig>;
  buttonAlign?: 'start' | 'center' | 'end';
};
