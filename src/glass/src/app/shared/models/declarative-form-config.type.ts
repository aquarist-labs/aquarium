import { AbstractControl, AsyncValidatorFn, ValidatorFn } from '@angular/forms';

import { Constraint } from '~/app/shared/models/constraint.type';

export type FormFieldModifier = {
  type: 'readonly' | 'value';
  constraint: Constraint;
  // Apply the opposite type, e.g. `editable` for `readonly`,
  // if the constraint is falsy. Defaults to `true`.
  opposite?: boolean;
  // Optional configuration data. This is required by the 'value'
  // modifier for example to set a specific value when the
  // constraint is truthy.
  data?: any;
};

export type FormFieldConfig = {
  name?: string;
  type:
    | 'text'
    | 'number'
    | 'password'
    | 'checkbox'
    | 'radio'
    | 'select'
    | 'hidden'
    | 'binary'
    | 'container'
    | 'divider'
    | 'paragraph';
  label?: string;
  value?: any;
  placeholder?: string;
  readonly?: boolean;
  autofocus?: boolean;
  hint?: string;
  groupClass?: string;
  // Modify the form field when the specified constraint is truthy.
  modifiers?: FormFieldModifier[];
  validators?: {
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    required?: boolean;
    requiredIf?: Constraint;
    pattern?: string | RegExp;
    patternType?: 'hostAddress';
    constraint?: {
      constraint: Constraint;
      errorMessage: string;
    };
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

  // --- divider ---
  title?: string;

  // --- paragraph ---
  text?: string;

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
  title?: string;
  subtitle?: string;
  fields: FormFieldConfig[];
  buttons?: Array<FormButtonConfig>;
  buttonAlign?: 'start' | 'center' | 'end';
};
