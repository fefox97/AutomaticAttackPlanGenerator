
import json
from datetime import datetime
from io import BytesIO

import pandas as pd

from apps.authentication.models import Users
from apps.risk_analysis import blueprint
from flask import render_template, request, send_file
from flask_security import auth_required, current_user

from flask import current_app as app
from apps.databases.models import App, AttackView, Capec, MacmUser, MethodologyCatalogue, MethodologyView, Macm, ThreatModel, ToolCatalogue, PentestPhases, ThreatAgentQuestionReplies, ThreatAgentQuestion, ThreatAgentReply, ThreatAgentReplyCategory, ThreatAgentCategory, ThreatAgentAttributesCategory, ThreatAgentAttribute, ThreatAgentRiskScores, StrideImpactRecord, ThreatAgentQuestionReplies, RiskRecord
from sqlalchemy import func
from apps.my_modules import converter, RiskAnalysisCatalogUtils
from apps import db

from flask_security import auth_required

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'risk_analysis'
        return segment
    except:
        return None


@blueprint.route('/macm_riskRating', methods=['GET'])
@auth_required()
def macm_riskRating():
    riskAnalysisCatalogUtils = RiskAnalysisCatalogUtils()
    selected_macm = request.args.get('app_id')

    try:
        # Recupera i dati relativi a Macm
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        app_info = App.query.filter_by(AppID=selected_macm).first()
        if len(table) == 0:
            table = None
    except Exception as e:
        app.logger.error(f"Error fetching table data for macm_riskRating: {e}", exc_info=True)
        table = None

    try:
        # Calcola le minacce per ciascun componente
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(
            ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)

        # Calcola il numero totale di minacce
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
    except Exception as e:
        app.logger.error(f"Error fetching threat data: {e}", exc_info=True)
        threat_for_each_component = {}
        threat_number = 0

    # Calcolo degli ID dei componenti analizzati
    try:
        analyzed_components = (
            db.session.query(RiskRecord.ComponentID)
            .filter_by(AppID=selected_macm)
            .distinct()
            .all()
        )
        analyzed_component_ids = [c[0] for c in analyzed_components]
    except Exception as e:
        app.logger.error(f"Error fetching analyzed components: {e}", exc_info=True)
        analyzed_component_ids = []

    # Calcola se il passo finale è stato completato (verifica se tutti i componenti hanno almeno un rischio associato)
    components_with_threats = {t.Component_ID for t in ThreatModel.query.filter_by(AppID=selected_macm).all()}
    components_with_risk = {r.ComponentID for r in RiskRecord.query.filter_by(AppID=selected_macm).all()}
    final_step_completed = components_with_threats.issubset(components_with_risk)

    # Rendering del template con i calcoli effettuati
    template = f"risk-analysis/macm_riskRating.html"
    return render_template(
        template,
        segment=get_segment(request),
        table=table,
        threat_for_each_component=threat_for_each_component,
        threat_number=threat_number,
        selected_macm=selected_macm,
        wizard_completed=riskAnalysisCatalogUtils.wizard_completed(selected_macm),
        stride_impact_completed=riskAnalysisCatalogUtils.stride_impact_completed(selected_macm), app_info=app_info,
        analyzed_component_ids=analyzed_component_ids,
        final_step_completed=final_step_completed
    )

@blueprint.route('/', methods=['GET'])
@auth_required()
def risk_analysis():
    try:
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        risk_analyses = MacmUser.query.join(App).filter(MacmUser.UserID==current_user.id).with_entities(App.AppID, App.Name.label('AppName'), App.Created_at.label('CreatedAt'), MacmUser.IsOwner).all()
        if len(risk_analyses) == 0:
            risk_analyses = None
    except Exception as error:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        raise error
    return render_template(f"risk-analysis/risk_analysis.html",
                           segment=get_segment(request),
                           risk_analyses=risk_analyses,
                           users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict)

@blueprint.route('/threat-agent-wizard', methods=['GET'])
@auth_required()
def threat_agent_wizard():
    context = {}
    appId = request.args.get('app_id')
    risk_analyses = request.args.get('risk_analyses')
    users = request.args.get('users')
    usersPerApp = request.args.get('usersPerApp')
    owners = request.args.get('owners')
    users_dict = request.args.get('users_dict')

    try:
        # Fetch all questions
        questions = ThreatAgentQuestion.query.all()

        # Initialize list to store question and its replies
        questions_replies_list = []

        # Loop through questions
        for question in questions:
            replies = []
            # Fetch replies for the current question
            question_replies = ThreatAgentQuestionReplies.query.filter_by(Question_id=question.Id).all()
            print(question_replies,question.Id)
            for question_reply in question_replies:
                reply_id = question_reply.Reply_id
                # Fetch the ThreatAgentReply
                reply = ThreatAgentReply.query.filter_by(Id=reply_id).first()
                print(reply)
                if reply:
                    replies.append({
                        'id': reply.Id,  # ID della risposta
                        'text': reply.Reply,  # Testo della risposta
                        'multiple': reply.Multiple,  # Indica se è multipla o no
                        'details': reply.Details  # Dettagli della risposta
                    })

            # Add question and corresponding replies to the list
            questions_replies_list.append({
                'id': question.Id,  # ID della domanda
                'question': question.Question,
                'replies': replies
            })

        # Add the questions and replies to the context
        context['questions_replies'] = questions_replies_list
        context['appId'] = appId
        print(questions_replies_list)

    except Exception as e:
        app.logger.error(f"Error occurred while fetching questions or replies: {e}", exc_info=True)
        context['questions_replies'] = None
    # Render the template with the context data
    return render_template(
        "risk-analysis/threat_agent_wizard.html",
        segment=get_segment(request),
        risk_analyses=risk_analyses,
        users=users,
        usersPerApp=usersPerApp,
        owners=owners,
        users_dict=users_dict,
        questions_replies=questions_replies_list,
        appId=appId
    )

@blueprint.route('/submit-questionnaire', methods=['POST'])
@auth_required()
def submit_questionnaire():
    if request.method == 'POST':
        riskAnalysisCatalogUtils = RiskAnalysisCatalogUtils()
        # Initialize a dictionary to store the user's responses
        user_responses = {}
        appId = request.form.get('appId')
        # Loop through the POST data to collect answers for each question
        for key, value in request.form.items():
            # The question ID is embedded in the "name" attribute, so we extract it
            if key.startswith('question_'):
                question_id = key.split('_')[1]

                # If the key ends with '[]', it means this is a multiple choice question (checkboxes)
                if '[]' in key:
                    # Remove '[]' from the key
                    question_id = question_id.replace('[]', '')
                    user_responses[question_id] = request.form.getlist(key)
                else:
                    user_responses[question_id] = value

        # Question Number 1
        Q1 = user_responses['1']
        Q1relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q1).all()

        # Question Number 2
        Q2 = user_responses['2']
        Q2relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q2).all()

        # Question Number 3
        Q3s = user_responses['3']
        Q3sResults = []
        for Q3 in Q3s:
            Q3relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q3).all()
            Q3sResults.append(set(Q3relatedCategories))  # Convert to set for easier merging

        # Unione progressiva per Q3
        Q3Merged = Q3sResults[0] if Q3sResults else set()
        for Q3Result in Q3sResults[1:]:
            Q3Merged = Q3Merged.union(Q3Result)

        # Question Number 4
        Q4s = user_responses['4']
        Q4sResults = []
        for Q4 in Q4s:
            Q4relatedCategories = ThreatAgentReplyCategory.query.filter_by(Reply_id=Q4).all()
            Q4sResults.append(set(Q4relatedCategories))  # Convert to set for easier merging

        # Unione progressiva per Q4
        Q4Merged = Q4sResults[0] if Q4sResults else set()
        for Q4Result in Q4sResults[1:]:
            Q4Merged = Q4Merged.union(Q4Result)


        ThreatAgents=Q1relatedCategories
        ThreatAgents = riskAnalysisCatalogUtils.intersect_threat_agents(ThreatAgents, set(Q2relatedCategories))
        ThreatAgents = riskAnalysisCatalogUtils.intersect_threat_agents(ThreatAgents, Q3Merged)
        ThreatAgents = riskAnalysisCatalogUtils.intersect_threat_agents(ThreatAgents, Q4Merged)
        ThreatAgents= riskAnalysisCatalogUtils.remove_duplicates_by_category_id(ThreatAgents)
        ThreatAgentsList=[]
        for threatAgent in ThreatAgents:
            category = ThreatAgentCategory.query.filter_by(Id=threatAgent.Category_id).first()
            if category:
                attributes=[]
                AttributesCategory = ThreatAgentAttributesCategory.query.filter_by(Category_id=category.Id).all()
                for attribute_category in AttributesCategory:
                    attribute=ThreatAgentAttribute.query.filter_by(Id=attribute_category.Attribute_id).first()
                    attributes.append(attribute)
                ThreatAgentsList.append({
                    'category': category,
                    'attributes': attributes
                })
        # Process the responses and generate threat agents based on the responses
        # threat_agents = generate_threat_agents(user_responses)

        # Pass the generated threat agents to the template
        return render_template(
            "risk-analysis/threat_agent_rating.html",
            segment=get_segment(request),
            user_responses=user_responses,
            ThreatAgents=ThreatAgentsList,
            appId=appId
        )


@blueprint.route('/threat_agent_evaluation', methods=['POST'])
@auth_required()
def threat_agent_evaluation():
    """
    Endpoint to evaluate threat agents for a given application and calculate OWASP risk scores.
    """
    # Extract `appId` and `objective` from the form
    riskAnalysisCatalogUtils = RiskAnalysisCatalogUtils()
    objective = request.form.get('objective', 'riskanalysis')  # Default to 'riskanalysis'
    appId = request.form.get('appId')

    # Initialize variables for reports and data analysis
    reports = []
    table = None
    threat_for_each_component = None
    threat_number = 0

    try:
        # Fetch distinct reports for the given `appId`
        reports = (
            AttackView.query.filter_by(AppID=appId)
            .with_entities(
                AttackView.Attack_Number,
                AttackView.Tool_ID,
                AttackView.Tool_Name,
                AttackView.Attack_Pattern,
                AttackView.Capec_ID,
                AttackView.Threat_ID,
                AttackView.Asset_Type,
                AttackView.Threat,
                AttackView.Component_ID,
                AttackView.Asset,
                AttackView.AppID,
                AttackView.ReportFiles,
                AttackView.Report_Parser
            )
            .where(AttackView.ReportFiles.isnot(None))
            .distinct()
            .all()
        )

        # Fetch table data for the given `appId`
        table = Macm.query.filter_by(App_ID=appId).all()
        if not table:
            table = None
    except Exception as e:
        app.logger.error(f"Error fetching reports or table for appId {appId}: {e}", exc_info=True)

    try:
        # Count attacks and threats for each component
        attack_for_each_component = AttackView.query.filter_by(AppID=appId).with_entities(
            AttackView.Component_ID, func.count(AttackView.Component_ID)
        ).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)

        threat_for_each_component = ThreatModel.query.filter_by(AppID=appId).with_entities(
            ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)
        ).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)

        threat_number = ThreatModel.query.filter_by(AppID=appId).count()
    except Exception as e:
        app.logger.error(f"Error fetching attacks or threats for appId {appId}: {e}", exc_info=True)



    # OWASP scoring variables
    OWASP_Motive_Total = 0
    OWASP_Size_Total = 0
    OWASP_Opportunity_Total = 0
    OWASP_Skill_Total = 0
    total_weights = 0
    category_details_list = []

    try:
        # Dictionaries to store category, attribute, and rating data
        category_ids = {}
        attribute_ids = {}
        ratings = {}
        rating_map = {'L': 1, 'M': 2, 'H': 3}  # Risk level mapping

        # Parse category, attribute, and rating information from the form
        for key in request.form.keys():
            if key.startswith("categoryId_"):
                category_name = key.split("categoryId_")[1]
                category_ids[category_name] = request.form.get(key)
            elif key.startswith("attributeId_"):
                parts = key.split("_")
                category_name = parts[1]
                attribute_name = "_".join(parts[2:])
                if category_name not in attribute_ids:
                    attribute_ids[category_name] = {}
                attribute_ids[category_name][attribute_name] = request.form.get(key)
            elif key.startswith("rating_"):
                category_name = key.split("rating_")[1]
                ratings[category_name] = request.form.get(key)

        # Process each category and calculate OWASP risk scores
        for category_name, category_id in category_ids.items():
            category_details = {}

            # Fetch the category and its attributes from the database
            category = ThreatAgentCategory.query.filter_by(Id=category_id).first()
            if not category:
                continue  # Skip invalid categories

            category_attributes = ThreatAgentAttributesCategory.query.filter_by(Category_id=category.Id).all()
            attributes = [
                ThreatAgentAttribute.query.filter_by(Id=attr.Attribute_id).first()
                for attr in category_attributes
            ]

            # Calculate OWASP parameters based on attribute scores
            rating = ratings.get(category_name)
            rating_score = rating_map.get(rating, 0)
            motive = size = opportunity = skill = 0
            limits = intent = access = resources = visibility = skills = 0

            for attribute in attributes:
                if attribute.Attribute == 'Skills':
                    skills = attribute.Score
                elif attribute.Attribute == 'Resources':
                    resources = attribute.Score
                elif attribute.Attribute == 'Visibility':
                    visibility = attribute.Score
                elif attribute.Attribute == 'Limits':
                    limits = attribute.Score
                elif attribute.Attribute == 'Intent':
                    intent = attribute.Score
                elif attribute.Attribute == 'Access':
                    access = attribute.Score

            # Compute individual OWASP parameters
            motive = ((((intent / 2) + (limits / 4)) / 2) * 10)
            opportunity = ((((access / 2) + (resources / 6) + (visibility / 4)) / 3) * 10)
            size = (resources / 6) * 10
            skill = (skills / 4) * 10

            # Accumulate weighted totals
            OWASP_Motive_Total += motive * rating_score
            OWASP_Opportunity_Total += opportunity * rating_score
            OWASP_Size_Total += size * rating_score
            OWASP_Skill_Total += skill * rating_score
            total_weights += rating_score

        # Normalize scores based on total weights
        if total_weights > 0:
            OWASP_Motive_Total = int(round(OWASP_Motive_Total / total_weights))
            OWASP_Opportunity_Total = int(round(OWASP_Opportunity_Total / total_weights))
            OWASP_Size_Total = int(round(OWASP_Size_Total / total_weights))
            OWASP_Skill_Total = int(round(OWASP_Skill_Total / total_weights))
        else:
            OWASP_Motive_Total = OWASP_Opportunity_Total = OWASP_Size_Total = OWASP_Skill_Total = 0
        
        try:
            # Save calculated scores to the database
            risk_score = ThreatAgentRiskScores.query.filter_by(AppID=appId).first()
            if risk_score:
                app.logger.info("Updating existing ThreatAgentRiskScores record")
                ThreatAgentRiskScores.query.filter_by(AppID=appId).update({
                    'Motive': OWASP_Motive_Total,
                    'Opportunity': OWASP_Opportunity_Total,
                    'Size': OWASP_Size_Total,
                    'Skill': OWASP_Skill_Total,
                })
            else:
                app.logger.info("Creating new ThreatAgentRiskScores record")
                risk_score = ThreatAgentRiskScores(
                    AppID=appId,
                    Motive=OWASP_Motive_Total,
                    Opportunity=OWASP_Opportunity_Total,
                    Size=OWASP_Size_Total,
                    Skill=OWASP_Skill_Total,
                    Created_at=datetime.utcnow(),
                    Uploaded_at=datetime.utcnow()
                )
                db.session.add(risk_score)
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Error saving OWASP risk scores: {e}", exc_info=True)
            db.session.rollback()

    except Exception as e:
        app.logger.error(f"Error processing threat agent evaluation: {e}", exc_info=True)

    analyzed_component_ids, final_step_completed = riskAnalysisCatalogUtils.completed_risk_analysis(appId)


    # Render the appropriate template
    template = "risk-analysis/macm_riskRating.html"
    return render_template(
        template,
        segment=get_segment(request),
        table=table,
        threat_for_each_component=threat_for_each_component,
        threat_number=threat_number,
        reports=reports,
        appId=appId,
        wizard_completed=True,
        stride_impact_completed=riskAnalysisCatalogUtils.stride_impact_completed(appId),
        analyzed_component_ids=analyzed_component_ids,
        final_step_completed=final_step_completed
    )


@blueprint.route('/stride-impact-rating', methods=['GET'])
@auth_required()
def stride_impact_rating():
    """
    Endpoint to evaluate STRIDE impact for a given application.
    """
    # Extract `appId` and `objective` from the form
    appId = request.args.get('app_id')

    stride_impact_evaluation_list=StrideImpactRecord.query.filter_by(AppID=appId).all()

    stride_impact_previous_results={}

    strides = ['spoofing', 'tampering', 'reputation', 'information_disclosure', 'dos', 'elevationofprivileges']
    for stride in strides:
        impact_per_stride = []
        impact_per_stride.append(5)
        impact_per_stride.append(5)
        impact_per_stride.append(5)
        impact_per_stride.append(5)
        stride_impact_previous_results[stride] = impact_per_stride
        stride_impact_previous_results["Created_at"] = None
        stride_impact_previous_results["Updated_at"] = None

    for stride_impact_evaluation in stride_impact_evaluation_list:
        impact_per_stride = []
        impact_per_stride.append(stride_impact_evaluation.Financialdamage)
        impact_per_stride.append(stride_impact_evaluation.Reputationdamage)
        impact_per_stride.append(stride_impact_evaluation.Noncompliance)
        impact_per_stride.append(stride_impact_evaluation.Privacyviolation)
        stride_impact_previous_results[stride_impact_evaluation.Stride] = impact_per_stride
        stride_impact_previous_results["Created_at"] = stride_impact_evaluation.Created_at

        # Modifica per troncare Updated_at ai secondi (rimuovendo i millisecondi)
        if stride_impact_evaluation.Updated_at:
            # Tronca il datetime ai secondi
            truncated_datetime = stride_impact_evaluation.Updated_at.replace(microsecond=0)
            stride_impact_previous_results["Updated_at"] = truncated_datetime
        else:
            stride_impact_previous_results["Updated_at"] = None




    template = "risk-analysis/stride_impact_risk.html"
    return render_template(
        template,
        segment=get_segment(request),appId=appId,
        stride_impact_previous_results=stride_impact_previous_results
    )


@blueprint.route('/stride_impact_evaluation', methods=['POST'])
@auth_required()
def stride_impact_evaluation():
    threatAgentUtils= RiskAnalysisCatalogUtils()
    """
    Endpoint to evaluate STRIDE impact for a given application.
    """
    appId = request.form.get('appId')

    # Initialize variables for reports and data analysis
    reports = []
    table = None
    attack_for_each_component = None
    attack_number = 0
    threat_for_each_component = None
    threat_number = 0

    try:
        # Fetch distinct reports for the given `appId`
        reports = (
            AttackView.query.filter_by(AppID=appId)
            .with_entities(
                AttackView.Attack_Number,
                AttackView.Tool_ID,
                AttackView.Tool_Name,
                AttackView.Attack_Pattern,
                AttackView.Capec_ID,
                AttackView.Threat_ID,
                AttackView.Asset_Type,
                AttackView.Threat,
                AttackView.Component_ID,
                AttackView.Asset,
                AttackView.AppID,
                AttackView.ReportFiles,
                AttackView.Report_Parser
            )
            .where(AttackView.ReportFiles.isnot(None))
            .distinct()
            .all()
        )

        # Fetch table data for the given `appId`
        table = Macm.query.filter_by(App_ID=appId).all()
        if not table:
            table = None
    except Exception as e:
        app.logger.error(f"Error fetching reports or table for appId {appId}: {e}", exc_info=True)

    try:
        # Count attacks and threats for each component
        attack_for_each_component = AttackView.query.filter_by(AppID=appId).with_entities(
            AttackView.Component_ID, func.count(AttackView.Component_ID)
        ).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)

        attack_number = AttackView.query.filter_by(AppID=appId).count()

        threat_for_each_component = ThreatModel.query.filter_by(AppID=appId).with_entities(
            ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)
        ).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)

        threat_number = ThreatModel.query.filter_by(AppID=appId).count()
    except Exception as e:
        app.logger.error(f"Error fetching attacks or threats for appId {appId}: {e}", exc_info=True)


    # STRIDE categories
    strides = ['spoofing', 'tampering', 'reputation', 'information_disclosure', 'dos', 'elevationofprivileges']
    stride_data = {}

    # Manually mapping specific strides to the correct readable format
    mapping = {
        'spoofing': 'Spoofing',
        'tampering': 'Tampering',
        'reputation': 'Reputation',
        'information_disclosure': 'Information Disclosure',
        'dos': 'Denial of Service',
        'elevationofprivileges': 'Elevation of Privileges'
    }

    for stride in strides:
        stride_data[stride] = {
            "financialdamage": int(request.form.get(f"{stride}_financialdamage", 0)),
            "reputationdamage": int(request.form.get(f"{stride}_reputationdamage", 0)),
            "noncompliance": int(request.form.get(f"{stride}_noncompliance", 0)),
            "privacyviolation": int(request.form.get(f"{stride}_privacyviolation", 0)),
        }

    for stride, impacts in stride_data.items():
        # Usa il metodo per aggiornare o creare il record
        StrideImpactRecord.update_or_create(
            app_id=appId,
            stride=stride,
            financialdamage=impacts['financialdamage'],
            reputationdamage=impacts['reputationdamage'],
            noncompliance=impacts['noncompliance'],
            privacyviolation=impacts['privacyviolation']
        )

    riskAnalysisCatalogUtils = RiskAnalysisCatalogUtils()
    analyzed_component_ids, final_step_completed = riskAnalysisCatalogUtils.completed_risk_analysis(appId)

    template = "risk-analysis/macm_riskRating.html"
    return render_template(
        template,
        segment=get_segment(request),
        table=table,
        attack_for_each_component=attack_for_each_component,
        attack_number=attack_number,
        threat_for_each_component=threat_for_each_component,
        threat_number=threat_number,
        reports=reports,
        appId=appId,
        wizard_completed=threatAgentUtils.wizard_completed(appId),
        stride_impact_completed=threatAgentUtils.stride_impact_completed(appId),
        analyzed_component_ids=analyzed_component_ids,
        final_step_completed=final_step_completed
    )

@blueprint.route('/macm-detailRisk', methods=['GET'])
def macm_riskDetailed():
    riskAnalysisCatalogUtils = RiskAnalysisCatalogUtils()
    try:
        selected_macm = request.args.get('app_id')
        selected_id = request.args.get('id')
        macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
        threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)

    ThreatAgentParameters= ThreatAgentRiskScores.query.filter_by(AppID=selected_macm).first()
    #calcolo stride impact
    form_data = {}
    app.logger.info(f"ThreatAgentParameters: {ThreatAgentParameters}")
    if ThreatAgentParameters:
        form_data['size']=ThreatAgentParameters.Size
        form_data['motive']=ThreatAgentParameters.Motive
        form_data['opportunity']=ThreatAgentParameters.Opportunity
        form_data['skill']=ThreatAgentParameters.Skill
    else:
        form_data['size']=5
        form_data['motive']=5
        form_data['opportunity']=5
        form_data['skill']=5

    # Iterate through each threat
    for threat in threat_data:
        # Check if the risk record already exists for this AppID, ComponentID, and ThreatID
        existing_risk = RiskRecord.query.filter_by(
            AppID=selected_macm,
            ComponentID=selected_id,
            ThreatID=threat.Threat_ID
        ).first()

        if existing_risk:
            # If a risk record already exists, skip the risk calculation
            app.logger.info(f"Risk record exists for Threat {threat.Threat} - Using existing record")
            form_data[threat.Threat] = {
                "threat": threat.Threat,
                "description": threat.Threat_Description,
                "stride": riskAnalysisCatalogUtils.map_stride(threat.STRIDE),
                "financialdamage": existing_risk.Financialdamage,
                "reputationdamage": existing_risk.Reputationdamage,
                "noncompliance": existing_risk.Noncompliance,
                "privacyviolation": existing_risk.Privacyviolation,
                # set the other values from the RiskRecord
                "ease_of_discovery": existing_risk.Easyofdiscovery,
                "ease_of_exploit": existing_risk.Easyofexploit,
                "awareness": existing_risk.Awareness,
                "intrusion_detection": existing_risk.Intrusiondetection,
                "loss_of_confidentiality": existing_risk.Lossconfidentiality,
                "loss_of_integrity": existing_risk.Lossintegrity,
                "loss_of_availability": existing_risk.Lossavailability,
                "loss_of_accountability": existing_risk.Lossaccountability,
            }
        else:
            # If no risk record exists, calculate and store the new values
            category_max = {
                "Financialdamage": {"max_value": 0, "stride": None, "record": None},
                "Reputationdamage": {"max_value": 0, "stride": None, "record": None},
                "Noncompliance": {"max_value": 0, "stride": None, "record": None},
                "Privacyviolation": {"max_value": 0, "stride": None, "record": None},
            }

            # Iterate over each STRIDE element for the threat
            for stride in riskAnalysisCatalogUtils.reverse_map_stride(threat.STRIDE):
                stride_impact = StrideImpactRecord.query.filter_by(AppID=selected_macm, Stride=stride).first()
                if stride_impact:
                    # Update maximums and store details for each category
                    for category in category_max.keys():
                        current_value = getattr(stride_impact, category)
                        if current_value > category_max[category]["max_value"]:
                            category_max[category] = {
                                "max_value": current_value,
                                "stride": stride,
                                "record": stride_impact,
                            }

            # Store detailed results for the threat
            form_data[threat.Threat] = {
                "threat": threat.Threat,
                "description": threat.Threat_Description,
                "stride": riskAnalysisCatalogUtils.map_stride(threat.STRIDE),
                "financialdamage": category_max["Financialdamage"]["max_value"],
                "reputationdamage": category_max["Reputationdamage"]["max_value"],
                "noncompliance": category_max["Noncompliance"]["max_value"],
                "privacyviolation": category_max["Privacyviolation"]["max_value"],
            }

            # set catalogue-based parameters 'ease_of_discovery', 'ease_of_exploit', 'awareness', 'intrusion_detection']
            form_data[threat.Threat]['ease_of_discovery'] = threat.EasyOfDiscovery
            form_data[threat.Threat]['ease_of_exploit'] = threat.EasyOfExploit
            form_data[threat.Threat]['awareness'] = threat.Awareness
            form_data[threat.Threat]['intrusion_detection'] = threat.IntrusionDetection
            form_data[threat.Threat]['loss_of_confidentiality'] = threat.LossOfConfidentiality
            form_data[threat.Threat]['loss_of_integrity'] = threat.LossOfIntegrity
            form_data[threat.Threat]['loss_of_availability'] = threat.LossOfAvailability
            form_data[threat.Threat]['loss_of_accountability'] = threat.LossOfAccountability

    riskAnalysisCatalogUtils = RiskAnalysisCatalogUtils()
    analyzed_component_ids, final_step_completed = riskAnalysisCatalogUtils.completed_risk_analysis(selected_macm)


    return render_template(f"risk-analysis/macm-detailRisk.html", segment=get_segment(request),
                            selected_macm=selected_macm, component_id=selected_id,
                            macm_data=macm_data, threat_data=threat_data,
                            ThreatAgentParameters=ThreatAgentParameters, form_data=form_data,
                            analyzed_component_ids=analyzed_component_ids,
                            final_step_completed=final_step_completed)


@blueprint.route('/save_risk_evaluation', methods=['POST'])
def save_risk_evaluation():
    threatAgentUtils = RiskAnalysisCatalogUtils()

    selected_macm = request.form.get('selected_macm')
    component_id = request.form.get('component_id')
    form = request.form

    try:
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if not table:
            table = None
    except Exception:
        table = None

    try:
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm)\
            .with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID))\
            .group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = threatAgentUtils.converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
    except Exception:
        app.logger.error('Exception while fetching threat data', exc_info=True)
        threat_for_each_component = {}
        threat_number = 0

    threat_ids = threatAgentUtils.get_all_threat_ids(form)

    for threat_id in threat_ids:
        threat_data = {
            key.split('[')[1][:-1]: value
            for key, value in form.items()
            if key.startswith(f"{threat_id}[") and key.endswith("]")
        }

        likelihood_value, likelihood_category = threatAgentUtils.calculate_likelihood(threat_data)
        tech_impact_value, bus_impact_value, tech_category, bus_category = threatAgentUtils.calculate_impact(threat_data)
        avg_impact = (tech_impact_value + bus_impact_value) / 2
        impact_category = threatAgentUtils.get_category(avg_impact)
        overall_risk = threatAgentUtils.calculate_overall_risk(likelihood_category, impact_category)

        risk_record = RiskRecord.query.filter_by(
            AppID=selected_macm,
            ComponentID=component_id,
            ThreatID=threat_id
        ).first()

        if risk_record:
            risk_record.Likelihood = int(round(likelihood_value))
            risk_record.TecnicalImpact = int(round(tech_impact_value))
            risk_record.BusinessImpact = int(round(bus_impact_value))
            risk_record.OverallRisk = overall_risk
            risk_record.updated_at = datetime.utcnow()
        else:
            new_risk_record = RiskRecord(
                AppID=selected_macm,
                ComponentID=component_id,
                ThreatID=threat_id,
                Skill=int(threat_data.get('skill', 5)),
                Size=int(threat_data.get('size', 5)),
                Motive=int(threat_data.get('motive', 5)),
                Opportunity=int(threat_data.get('opportunity', 5)),
                Easyofdiscovery=int(threat_data.get('ease_of_discovery', 5)),
                Easyofexploit=int(threat_data.get('ease_of_exploit', 5)),
                Awareness=int(threat_data.get('awareness', 5)),
                Intrusiondetection=int(threat_data.get('intrusion_detection', 5)),
                Lossconfidentiality=int(threat_data.get('loss_of_confidentiality', 5)),
                Lossintegrity=int(threat_data.get('loss_of_integrity', 5)),
                Lossavailability=int(threat_data.get('loss_of_availability', 5)),
                Lossaccountability=int(threat_data.get('loss_of_accountability', 5)),
                Financialdamage=int(threat_data.get('financialdamage', 5)),
                Reputationdamage=int(threat_data.get('reputationdamage', 5)),
                Noncompliance=int(threat_data.get('noncompliance', 5)),
                Privacyviolation=int(threat_data.get('privacyviolation', 5)),
                Likelihood=int(round(likelihood_value)),
                TecnicalImpact=int(round(tech_impact_value)),
                BusinessImpact=int(round(bus_impact_value)),
                TechnicalRisk=tech_category,
                OverallRisk=overall_risk
            )
            db.session.add(new_risk_record)
        db.session.commit()
    # Dopo db.session.commit()
    analyzed_components = (
        db.session.query(RiskRecord.ComponentID)
        .filter_by(AppID=selected_macm)
        .distinct()
        .all()
    )
    analyzed_component_ids = [c[0] for c in analyzed_components]

    # Componenti che hanno almeno un threat
    components_with_threats = {t.Component_ID for t in ThreatModel.query.filter_by(AppID=selected_macm).all()}

    # Componenti che hanno almeno un RiskRecord
    components_with_risk = {r.ComponentID for r in RiskRecord.query.filter_by(AppID=selected_macm).all()}

    final_step_completed=components_with_threats.issubset(components_with_risk)

    template = f"risk-analysis/macm_riskRating.html"
    return render_template(
        template,
        segment=get_segment(request),
        table=table,
        threat_for_each_component=threat_for_each_component,
        threat_number=threat_number,
        selected_macm=selected_macm,
        wizard_completed=threatAgentUtils.wizard_completed(selected_macm),
        stride_impact_completed=threatAgentUtils.stride_impact_completed(selected_macm),
        analyzed_component_ids=analyzed_component_ids,
        final_step_completed=final_step_completed
    )



@blueprint.route('/final-step', methods=['GET'])
@login_required
def final_step():
    selected_macm = request.args.get('app_id')

    # Recupera i record di rischio associati all'AppID selezionato
    risk_records = RiskRecord.query.filter_by(AppID=selected_macm).all()

    # Organizza i dati per esportarli
    data = []
    for record in risk_records:
        # Ottieni asset dal modello 'Macm' (presumendo che esista una relazione in RiskRecord -> Macm)
        asset = Macm.query.filter_by(Component_ID=record.ComponentID).first()
        asset_name = asset.Name if asset else "Unknown"  # Recupera il nome dell'asset o "Unknown" se non trovato

        # Ottieni tutte le minacce associate al component_id dal modello 'ThreatModel'
        threat_models = (ThreatModel.query.filter_by(Threat_ID=record.ThreatID).all())

        for threat_model in threat_models:
            # Recupera il nome della minaccia o "Unknown"
            threat = threat_model.Threat if threat_model else "Unknown"

            # Aggiungi i dati per ciascuna minaccia associata all'asset
            data.append({
                "Asset": asset_name,
                "Threat": threat,
                "ComponentID": record.ComponentID,
                "FinancialDamage": record.Financialdamage,
                "ReputationDamage": record.Reputationdamage,
                "Noncompliance": record.Noncompliance,
                "PrivacyViolation": record.Privacyviolation,
                "Likelihood": record.Likelihood,
                "TechnicalImpact": record.TecnicalImpact,
                "BusinessImpact": record.BusinessImpact,
                "OverallRisk": record.OverallRisk,
                "EaseOfDiscovery": record.Easyofdiscovery,
                "EaseOfExploit": record.Easyofexploit,
                "Awareness": record.Awareness,
                "IntrusionDetection": record.Intrusiondetection,
                "LossOfConfidentiality": record.Lossconfidentiality,
                "LossOfIntegrity": record.Lossintegrity,
                "LossOfAvailability": record.Lossavailability,
                "LossOfAccountability": record.Lossaccountability
            })

    # Crea un DataFrame pandas dai dati
    df = pd.DataFrame(data)

    # Salva il DataFrame in un file Excel in memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='RiskAnalysis')
    output.seek(0)

    # Restituisci il file Excel come risposta
    return send_file(output, as_attachment=True, download_name=f'risk_analysis_{selected_macm}.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')