import React from 'react';
import Input2 from "./Form/Input2";
import {withRouter} from "react-router";
import Textarea2 from "./Form/Textarea2";


class TemplateForm extends React.Component {
    
    constructor(props) {
        super(props);
        this.state = {
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {template} = this.props;
        this.unsubscribe = template.subscribe(() => this.setState({saveDisabled: !template.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {template, onSave, onDelete} = this.props;
        const {saveDisabled} = this.state;
        
        return (
            <form className="uk-form uk-form-stacked" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                <Input2 model={template} name="name" title="Namn"/>
                <Input2 model={template} name="title" title="Titel"/>
                <Textarea2 model={template} name="description" title="Meddelande"/>
                
                <div className="uk-form-row">
                    <div className="uk-form-row">
                        {template.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash"/> Ta bort medlem</a> : ""}
                        <button className="uk-button uk-button-success uk-float-right" disabled={saveDisabled}><i className="uk-icon-save"/> {template.id ? 'Spara' : 'Skapa'}</button>
                    </div>
                </div>
            </form>
        );
    }
}


export default withRouter(TemplateForm);