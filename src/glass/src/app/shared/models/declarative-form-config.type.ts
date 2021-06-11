export type FormFieldConfig = {
  name: string;
  type: 'text' | 'number' | 'password' | 'token';
  label?: string;
  value?: any;
  readonly?: boolean;
  autofocus?: boolean;
  hint?: string;
  class?: string;
  validators?: {
    min?: number;
    max?: number;
    required?: boolean;
    pattern?: string | RegExp;
    patternType?: 'hostAddress';
  };
  onPaste?: (event: ClipboardEvent) => void;

  // text | password
  hasCopyToClipboardButton?: boolean;
};

export type DeclarativeFormConfig = {
  hint?: string;
  subtitle?: string;
  fields: FormFieldConfig[];
};
