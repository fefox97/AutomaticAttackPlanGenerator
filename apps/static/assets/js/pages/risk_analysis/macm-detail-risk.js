function calculateLikelihood(threatID) {
    var params = ['skill', 'motive', 'opportunity', 'size', 'ease_of_discovery', 'ease_of_exploit', 'awareness', 'intrusion_detection'];
    var sum = 0, count = 0;
    params.forEach(function(param) {
        var value = parseInt(document.getElementById(param + "_" + threatID).value) || 5;
        sum += value;
        count++;
        setColor(param + "_" + threatID, value);
    });
    var likelihood = sum / count;
    var likelihoodCategory = getCategory(likelihood);
    // Includi la categoria nel testo del badge
    document.getElementById("likelihood_" + threatID).innerText = "Likelihood: " + likelihood.toFixed(2) + " (" + likelihoodCategory + ")";
    setColor("likelihood_" + threatID, likelihood);
    calculateOverallRisk(threatID);
}

function calculateImpact(threatID) {
    var techParams = ['loss_of_confidentiality', 'loss_of_integrity', 'loss_of_availability', 'loss_of_accountability'];
    var busParams = ['financialdamage', 'reputationdamage', 'noncompliance', 'privacyviolation'];
    var techSum = 0, busSum = 0;
    techParams.forEach(param => {
        var value = parseInt(document.getElementById(param + "_" + threatID).value) || 5;
        techSum += value;
        setColor(param + "_" + threatID, value);
    });
    busParams.forEach(param => {
        var value = parseInt(document.getElementById(param + "_" + threatID).value) || 5;
        busSum += value;
        setColor(param + "_" + threatID, value);
    });
    var technicalImpact = techSum / techParams.length;
    var businessImpact = busSum / busParams.length;
    var techCategory = getCategory(technicalImpact);
    var busCategory = getCategory(businessImpact);
    // Includi le categorie nel testo dei badge
    document.getElementById("technical_impact_" + threatID).innerText = "Technical Impact: " + technicalImpact.toFixed(2) + " (" + techCategory + ")";
    document.getElementById("business_impact_" + threatID).innerText = "Business Impact: " + businessImpact.toFixed(2) + " (" + busCategory + ")";
    setColor("technical_impact_" + threatID, technicalImpact);
    setColor("business_impact_" + threatID, businessImpact);
    calculateOverallRisk(threatID);
}

function calculateOverallRisk(threatID) {
    // Leggi la categoria di Likelihood dal data attribute

    // Leggi le categorie di Technical e Business Impact dai data attributes
    var technicalImpactElement = document.getElementById("technical_impact_" + threatID);
    var businessImpactElement = document.getElementById("business_impact_" + threatID);
    var likelihoodElement = document.getElementById("likelihood_"+threatID);
    var technicalImpact = parseFloat(technicalImpactElement.innerText.split(':')[1]) ;
    var businessImpact = parseFloat(businessImpactElement.innerText.split(':')[1]) ;
    var likelihoodValue = parseFloat(likelihoodElement.innerText.split(':')[1]);
    var impact=parseFloat((technicalImpact+businessImpact)/2);
    // console.log("tecnical "+technicalImpact+" business "+businessImpact+" totale "+impact);

    // Determina la categoria di Impact
    var impactCategory = getCategory(impact);
    var likelihoodCategory = getCategory(likelihoodValue);

    // Calcola la categoria di Overall Risk
    var overallRiskCategory = calculateRiskCategory(likelihoodCategory, impactCategory);
    // console.log("categoriaImpatto "+impactCategory + " impatto "+ impact+  " categoriaLikelhood "+likelihoodCategory, " categoriaRischio "+overallRiskCategory);


    // Aggiorna il badge di Overall Risk
    var overallRiskElement = document.getElementById("overall_risk_" + threatID);
    overallRiskElement.innerText = "Overall Risk: " + overallRiskCategory;
    setColor(overallRiskElement.id, overallRiskCategory);
}

function calculateRiskCategory(likelihoodCategory, impactCategory) {
    // Define the risk matrix based on the uploaded image
    const riskMatrix = {
        Low: {
            Low: "Note",
            Medium: "Low",
            High: "Medium"
        },
        Medium: {
            Low: "Low",
            Medium: "Medium",
            High: "High"
        },
        High: {
            Low: "Medium",
            Medium: "High",
            High: "Critical"
        },
    };

    // Return the overall risk severity based on the matrix
    return riskMatrix[likelihoodCategory][impactCategory] || "Unknown";
}


function setColor(id, category) {
    var element = document.getElementById(id);

    // Ensure the element exists
    if (!element) {
        console.warn(`Element with ID "${id}" not found.`);
        return;
    }

    // Remove all risk-related classes
    element.classList.remove("critical", "high", "medium", "low", "note");

    // If category is a numeric value, convert it to a string category
    if (typeof category !== "string") {
        category = getCategory(category); // Convert numeric value to category
    }

    // Add the appropriate category class
    if (category && typeof category === "string") {
        element.classList.add(category.toLowerCase());
    } else {
        console.warn(`Invalid category provided to setColor: ${category}`);
    }
}

function getCategory(value) {
    if (value >= 7) {
        return "High";
    }
    if (value >= 4 && value < 7) {
        return "Medium";
    }
    return "Low";
}

$(document).ready(function() {
    for (const threat of threatData) {
        calculateLikelihood(threat.Threat_ID);
        calculateImpact(threat.Threat_ID);
        calculateOverallRisk(threat.Threat_ID);
    }

    document.getElementById('save_risk_evaluation').addEventListener('submit', function (event) {
        event.preventDefault();  // Impedisce il comportamento di submit predefinito

        const evaluationData = [];  // Array per raccogliere i dati delle minacce

        for (const threat of threatData) {
            const threatID = threat.Threat_ID;

            // Raccogliere i valori dei parametri di likelihood
            const likelihoodParams = ['skill', 'motive', 'opportunity', 'size', 'ease_of_discovery', 'ease_of_exploit', 'awareness', 'intrusion_detection'];
            const likelihoodData = {};
            likelihoodParams.forEach(param => {
                likelihoodData[param] = parseFloat(document.getElementById(`${param}_${threatID}`).value) || 5;
            });

            // Raccogliere i valori dei parametri di impact
            const impactParams = ['loss_of_confidentiality', 'loss_of_integrity', 'loss_of_availability', 'loss_of_accountability',
                                'financialdamage', 'reputationdamage', 'noncompliance', 'privacyviolation'];
            const impactData = {};
            impactParams.forEach(param => {
                impactData[param] = parseFloat(document.getElementById(`${param}_${threatID}`).value) || 5;
            });

            // Raccogliere i valori calcolati
            const likelihood = parseFloat(document.getElementById(`likelihood_${threatID}`).innerText.split(':')[1]) || 0;
            const technicalImpact = parseFloat(document.getElementById(`technical_impact_${threatID}`).innerText.split(':')[1]) || 0;
            const businessImpact = parseFloat(document.getElementById(`business_impact_${threatID}`).innerText.split(':')[1]) || 0;
            const overallRisk = document.getElementById(`overall_risk_${threatID}`).innerText.split(':')[1]?.trim() || "Unknown";

            // Costruire l'oggetto dei dati da inviare
            evaluationData.push({
                Threat_ID: threatID,
                Likelihood: likelihood,
                Technical_Impact: technicalImpact,
                Business_Impact: businessImpact,
                Overall_Risk: overallRisk,
                Likelihood_Params: likelihoodData,
                Impact_Params: impactData,
            });
        }

        // Preparare il payload da inviare
        const payload = {
            component_id: component_id,
            selected_macm: selected_macm,
            evaluation_data: evaluationData
        };

        // Inviare i dati al server tramite fetch
        fetch('/risk_analysis/save_risk_evaluation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            data: {
                component_id: component_id,
                selected_macm: selected_macm,
                evaluation_data: evaluationData
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Errore nella richiesta al server');
            }
            return response.json();
        })
        .then(data => {
            console.log('Risposta dal server:', data);
            alert('Dati salvati con successo!');
        })
        .catch(error => {
            console.error('Errore:', error);
            alert('Errore durante il salvataggio dei dati.');
        });
    });
});
