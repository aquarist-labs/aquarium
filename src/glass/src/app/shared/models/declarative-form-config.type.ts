import { AbstractControl, AsyncValidatorFn, ValidatorFn } from '@angular/forms';

export type FormFieldConfig = {
  name: string;
  type:
    | 'text'
    | 'number'
    | 'password'
    | 'checkbox'
    | 'radio'
    | 'select'
    | 'hidden'
    | 'binary'
    | 'container';
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
    // The custom validators must return an error object with
    // the property 'custom' for the error message.
    custom?: ValidatorFn;
    asyncCustom?: AsyncValidatorFn;
  };
  onPaste?: (event: ClipboardEvent) => void;
  onValueChanges?: (value: any, control: AbstractControl, form: DeclarativeForm) => void;

  // --- radio ---
  // Note, radio buttons behave different to other form fields.
  // The 'value' property defines what value is represented by
  // this form field. If you want to check it, then you need to
  // set the 'checked' property.
  checked?: boolean;

  // --- text | password ---
  hasCopyToClipboardButton?: boolean;

  // --- dropdown ---
  options?: Record<any, string>;

  // --- container ---
  fields?: Array<FormFieldConfig>;
  // Fields in a container will respect the 'flex' configuration.
  // Specifies the size of the field in percent.
  flex?: number;

  // --- binary ---
  defaultUnit?: 'b' | 'k' | 'm' | 'g' | 't' | 'p' | 'e' | 'z' | 'y';

  // internal only
  id?: string;
};

export type FormButtonConfig = {
  type: 'default' | 'submit';
  text?: string;
  class?: string;
  click?: (buttonConfig: FormButtonConfig, values: Record<string, any>) => void;
};

export type DeclarativeFormValues = Record<string, any>;

export interface DeclarativeForm {
  getControl(path: string): AbstractControl | null;
  get values(): DeclarativeFormValues;
  patchValues(values: DeclarativeFormValues): void;
}

export type DeclarativeFormConfig = {
  id?: string; // A unique form ID.
  hint?: string;
  subtitle?: string;
  fields: FormFieldConfig[];
  buttons?: Array<FormButtonConfig>;
  buttonAlign?: 'start' | 'center' | 'end';
};
